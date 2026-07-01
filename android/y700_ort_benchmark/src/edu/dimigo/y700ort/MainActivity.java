package edu.dimigo.y700ort;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

import ai.onnxruntime.OnnxJavaType;
import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class MainActivity extends Activity {
    private static final int WARMUP = 3;
    private static final int RUNS = 20;

    private TextView statusView;

    private static final ModelSpec[] MODELS = new ModelSpec[] {
            new ModelSpec("matvec_cpu_baseline.onnx", "float_matmul", 16, 4),
            new ModelSpec("matvec_int8_matmulinteger.onnx", "matmulinteger", 16, 4),
            new ModelSpec("gemma_attention_output_projection_1024x1152_float.onnx", "float_matmul", 1024, 1152),
            new ModelSpec("gemma_attention_output_projection_1024x1152_matmulinteger.onnx", "matmulinteger", 1024, 1152),
            new ModelSpec("gemma_lm_head_tile_1152x4096_float.onnx", "float_matmul", 1152, 4096),
            new ModelSpec("gemma_lm_head_tile_1152x4096_matmulinteger.onnx", "matmulinteger", 1152, 4096),
            new ModelSpec("gemma_mlp_projection_1152x6912_float.onnx", "float_matmul", 1152, 6912),
            new ModelSpec("gemma_mlp_projection_1152x6912_matmulinteger.onnx", "matmulinteger", 1152, 6912),
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        statusView = new TextView(this);
        statusView.setText("Running Y700 ONNX Runtime benchmark...");
        setContentView(statusView);
        new Thread(new Runnable() {
            @Override
            public void run() {
                runBenchmarks();
            }
        }).start();
    }

    private void runBenchmarks() {
        List<ResultRow> rows = new ArrayList<>();
        File outDir = new File(getExternalFilesDir(null), "y700_onnx_runtime");
        //noinspection ResultOfMethodCallIgnored
        outDir.mkdirs();
        try {
            OrtEnvironment env = OrtEnvironment.getEnvironment();
            String providers = OrtEnvironment.getAvailableProviders().toString();
            for (String ep : new String[] {"CPU", "NNAPI", "QNN"}) {
                for (ModelSpec model : MODELS) {
                    rows.add(runOne(env, model, ep, providers));
                    writeOutputs(outDir, rows, false);
                }
            }
            writeOutputs(outDir, rows, true);
            setStatus("Benchmark complete: " + outDir.getAbsolutePath());
        } catch (Throwable t) {
            ResultRow row = new ResultRow();
            row.modelName = "benchmark_app";
            row.executionProvider = "app";
            row.status = "app_error";
            row.error = sanitize(t.toString());
            rows.add(row);
            try {
                writeOutputs(outDir, rows, true);
            } catch (Exception ignored) {
                // The UI still shows the error if file writing fails.
            }
            setStatus("Benchmark failed: " + t);
        }
    }

    private ResultRow runOne(OrtEnvironment env, ModelSpec model, String ep, String availableProviders) {
        ResultRow row = new ResultRow();
        row.modelName = model.name;
        row.kind = model.kind;
        row.executionProvider = ep;
        row.inputDim = model.inputDim;
        row.outputDim = model.outputDim;
        row.warmup = WARMUP;
        row.runs = RUNS;
        row.availableProviders = availableProviders;
        row.status = "unknown";
        long[] activationShape = new long[] {1, model.inputDim};
        long[] weightShape = new long[] {model.inputDim, model.outputDim};
        Map<String, OnnxTensor> inputs = new HashMap<>();

        try (OrtSession.SessionOptions opts = new OrtSession.SessionOptions()) {
            opts.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT);
            if ("NNAPI".equals(ep)) {
                opts.addNnapi();
            } else if ("QNN".equals(ep)) {
                opts.addQnn(new HashMap<String, String>());
            }

            byte[] modelBytes = readAsset(model.name);
            try (OrtSession session = env.createSession(modelBytes, opts)) {
                if ("float_matmul".equals(model.kind)) {
                    inputs.put("activation", OnnxTensor.createTensor(env, makeFloatBuffer(model.inputDim, 1), activationShape));
                    inputs.put("weight", OnnxTensor.createTensor(env, makeFloatBuffer(model.inputDim * model.outputDim, 3), weightShape));
                } else {
                    inputs.put("activation", OnnxTensor.createTensor(env, makeByteBuffer(model.inputDim, 1), activationShape, OnnxJavaType.INT8));
                    inputs.put("weight", OnnxTensor.createTensor(env, makeByteBuffer(model.inputDim * model.outputDim, 3), weightShape, OnnxJavaType.INT8));
                }

                for (int i = 0; i < WARMUP; i++) {
                    try (OrtSession.Result ignored = session.run(inputs)) {
                        // warmup
                    }
                }

                double[] latencies = new double[RUNS];
                for (int i = 0; i < RUNS; i++) {
                    long start = System.nanoTime();
                    try (OrtSession.Result ignored = session.run(inputs)) {
                        // measured run
                    }
                    latencies[i] = (System.nanoTime() - start) / 1_000_000.0;
                }
                row.status = "completed";
                fillStats(row, latencies);
            }
        } catch (Throwable t) {
            row.status = "integration_blocked";
            row.error = sanitize(t.toString());
        } finally {
            for (OnnxTensor tensor : inputs.values()) {
                tensor.close();
            }
        }
        return row;
    }

    private byte[] readAsset(String name) throws Exception {
        try (InputStream input = getAssets().open(name);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) >= 0) {
                output.write(buffer, 0, read);
            }
            return output.toByteArray();
        }
    }

    private FloatBuffer makeFloatBuffer(int count, int seed) {
        ByteBuffer bytes = ByteBuffer.allocateDirect(count * 4).order(ByteOrder.nativeOrder());
        FloatBuffer floats = bytes.asFloatBuffer();
        for (int i = 0; i < count; i++) {
            floats.put(((i * seed) % 17 - 8) / 8.0f);
        }
        floats.rewind();
        return floats;
    }

    private ByteBuffer makeByteBuffer(int count, int seed) {
        ByteBuffer bytes = ByteBuffer.allocateDirect(count).order(ByteOrder.nativeOrder());
        for (int i = 0; i < count; i++) {
            bytes.put((byte) (((i * seed) % 13) - 6));
        }
        bytes.rewind();
        return bytes;
    }

    private void fillStats(ResultRow row, double[] values) {
        double[] sorted = values.clone();
        Arrays.sort(sorted);
        double sum = 0.0;
        for (double value : values) {
            sum += value;
        }
        row.meanMs = sum / values.length;
        row.p50Ms = percentile(sorted, 0.50);
        row.p95Ms = percentile(sorted, 0.95);
        row.minMs = sorted[0];
        row.maxMs = sorted[sorted.length - 1];
    }

    private double percentile(double[] sorted, double q) {
        if (sorted.length == 1) {
            return sorted[0];
        }
        double pos = q * (sorted.length - 1);
        int lo = (int) Math.floor(pos);
        int hi = (int) Math.ceil(pos);
        if (lo == hi) {
            return sorted[lo];
        }
        double frac = pos - lo;
        return sorted[lo] * (1.0 - frac) + sorted[hi] * frac;
    }

    private void writeOutputs(File outDir, List<ResultRow> rows, boolean done) throws Exception {
        //noinspection ResultOfMethodCallIgnored
        outDir.mkdirs();
        try (FileOutputStream csv = new FileOutputStream(new File(outDir, "benchmark_y700_ort_android.csv"))) {
            csv.write(("model_name,kind,execution_provider,status,input_dim,output_dim,warmup,runs,mean_ms,p50_ms,p95_ms,min_ms,max_ms,available_providers,error\n").getBytes());
            for (ResultRow row : rows) {
                csv.write(row.toCsv().getBytes());
            }
        }
        try (FileOutputStream json = new FileOutputStream(new File(outDir, "benchmark_y700_ort_android.json"))) {
            json.write(toJson(rows, done).getBytes());
        }
        try (FileOutputStream marker = new FileOutputStream(new File(outDir, done ? "DONE" : "RUNNING"))) {
            marker.write((done ? "done\n" : "running\n").getBytes());
        }
    }

    private String toJson(List<ResultRow> rows, boolean done) {
        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"status\": \"").append(done ? "completed" : "running").append("\",\n");
        sb.append("  \"warmup\": ").append(WARMUP).append(",\n");
        sb.append("  \"runs\": ").append(RUNS).append(",\n");
        sb.append("  \"results\": [\n");
        for (int i = 0; i < rows.size(); i++) {
            if (i > 0) {
                sb.append(",\n");
            }
            sb.append(rows.get(i).toJsonObject());
        }
        sb.append("\n  ]\n");
        sb.append("}\n");
        return sb.toString();
    }

    private void setStatus(String text) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                statusView.setText(text);
            }
        });
    }

    private static String sanitize(String text) {
        if (text == null) {
            return "";
        }
        return text.replace('\n', ' ').replace('\r', ' ').replace(',', ';');
    }

    private static String csvEscape(String text) {
        String safe = text == null ? "" : text;
        return "\"" + safe.replace("\"", "\"\"") + "\"";
    }

    private static String jsonEscape(String text) {
        String safe = text == null ? "" : text;
        return safe.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static final class ModelSpec {
        final String name;
        final String kind;
        final int inputDim;
        final int outputDim;

        ModelSpec(String name, String kind, int inputDim, int outputDim) {
            this.name = name;
            this.kind = kind;
            this.inputDim = inputDim;
            this.outputDim = outputDim;
        }
    }

    private static final class ResultRow {
        String modelName = "";
        String kind = "";
        String executionProvider = "";
        String status = "";
        int inputDim = 0;
        int outputDim = 0;
        int warmup = 0;
        int runs = 0;
        double meanMs = Double.NaN;
        double p50Ms = Double.NaN;
        double p95Ms = Double.NaN;
        double minMs = Double.NaN;
        double maxMs = Double.NaN;
        String availableProviders = "";
        String error = "";

        String toCsv() {
            return String.join(",",
                    csvEscape(modelName),
                    csvEscape(kind),
                    csvEscape(executionProvider),
                    csvEscape(status),
                    Integer.toString(inputDim),
                    Integer.toString(outputDim),
                    Integer.toString(warmup),
                    Integer.toString(runs),
                    format(meanMs),
                    format(p50Ms),
                    format(p95Ms),
                    format(minMs),
                    format(maxMs),
                    csvEscape(availableProviders),
                    csvEscape(error)
            ) + "\n";
        }

        String toJsonObject() {
            return "    {"
                    + "\"model_name\":\"" + jsonEscape(modelName) + "\","
                    + "\"kind\":\"" + jsonEscape(kind) + "\","
                    + "\"execution_provider\":\"" + jsonEscape(executionProvider) + "\","
                    + "\"status\":\"" + jsonEscape(status) + "\","
                    + "\"input_dim\":" + inputDim + ","
                    + "\"output_dim\":" + outputDim + ","
                    + "\"warmup\":" + warmup + ","
                    + "\"runs\":" + runs + ","
                    + "\"mean_ms\":" + jsonNumber(meanMs) + ","
                    + "\"p50_ms\":" + jsonNumber(p50Ms) + ","
                    + "\"p95_ms\":" + jsonNumber(p95Ms) + ","
                    + "\"min_ms\":" + jsonNumber(minMs) + ","
                    + "\"max_ms\":" + jsonNumber(maxMs) + ","
                    + "\"available_providers\":\"" + jsonEscape(availableProviders) + "\","
                    + "\"error\":\"" + jsonEscape(error) + "\""
                    + "}";
        }

        private String format(double value) {
            return Double.isNaN(value) ? "" : String.format(Locale.US, "%.6f", value);
        }

        private String jsonNumber(double value) {
            return Double.isNaN(value) ? "null" : String.format(Locale.US, "%.6f", value);
        }
    }
}
