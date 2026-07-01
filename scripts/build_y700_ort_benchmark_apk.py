#!/usr/bin/env python3
"""Build a minimal Android ONNX Runtime benchmark APK without Gradle."""

from __future__ import annotations

import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANDROID_HOME = Path.home() / "Android" / "Sdk"
BUILD_TOOLS = ANDROID_HOME / "build-tools" / "35.0.0"
ANDROID_JAR = ANDROID_HOME / "platforms" / "android-35" / "android.jar"
APP = ROOT / "android" / "y700_ort_benchmark"
OUT = ROOT / "build" / "y700_ort_benchmark"
THIRD_PARTY = ROOT / "third_party" / "onnxruntime_android"
VERSION = "1.27.0"
AAR = THIRD_PARTY / f"onnxruntime-android-{VERSION}.aar"
APK = ROOT / "build" / "y700_ort_benchmark.apk"
SIGNED_APK = ROOT / "build" / "y700_ort_benchmark-signed.apk"
KEYSTORE = ROOT / "build" / "y700_ort_benchmark-debug.keystore"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_aar() -> None:
    THIRD_PARTY.mkdir(parents=True, exist_ok=True)
    if AAR.exists():
        return
    url = f"https://repo1.maven.org/maven2/com/microsoft/onnxruntime/onnxruntime-android/{VERSION}/onnxruntime-android-{VERSION}.aar"
    urllib.request.urlretrieve(url, AAR)


def main() -> None:
    ensure_aar()
    if not ANDROID_JAR.exists():
        raise SystemExit(f"missing Android platform jar: {ANDROID_JAR}")
    for tool in ["aapt2", "d8", "zipalign", "apksigner"]:
        if not (BUILD_TOOLS / tool).exists():
            raise SystemExit(f"missing Android build tool: {BUILD_TOOLS / tool}")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "aar").mkdir(parents=True)
    (OUT / "compiled_res").mkdir(parents=True)
    (OUT / "gen").mkdir(parents=True)
    (OUT / "classes").mkdir(parents=True)
    (OUT / "dex").mkdir(parents=True)
    (OUT / "apk").mkdir(parents=True)

    with zipfile.ZipFile(AAR) as zf:
        zf.extractall(OUT / "aar")

    for res in (APP / "res").rglob("*.xml"):
        run([str(BUILD_TOOLS / "aapt2"), "compile", "-o", str(OUT / "compiled_res"), str(res)])
    flat_files = sorted((OUT / "compiled_res").glob("*.flat"))

    linked = OUT / "linked.apk"
    run(
        [
            str(BUILD_TOOLS / "aapt2"),
            "link",
            "-I",
            str(ANDROID_JAR),
            "--manifest",
            str(APP / "AndroidManifest.xml"),
            "--min-sdk-version",
            "24",
            "--target-sdk-version",
            "35",
            "--java",
            str(OUT / "gen"),
            "-o",
            str(linked),
        ]
        + [str(p) for p in flat_files]
    )

    java_files = [str(p) for p in (APP / "src").rglob("*.java")] + [str(p) for p in (OUT / "gen").rglob("*.java")]
    run(
        [
            "javac",
            "-encoding",
            "UTF-8",
            "-source",
            "8",
            "-target",
            "8",
            "-bootclasspath",
            str(ANDROID_JAR),
            "-classpath",
            str(OUT / "aar" / "classes.jar"),
            "-d",
            str(OUT / "classes"),
        ]
        + java_files
    )

    run(
        [
            str(BUILD_TOOLS / "d8"),
            "--min-api",
            "23",
            "--lib",
            str(ANDROID_JAR),
            "--classpath",
            str(OUT / "aar" / "classes.jar"),
            "--output",
            str(OUT / "dex"),
        ]
        + [str(p) for p in (OUT / "classes").rglob("*.class")]
        + [str(OUT / "aar" / "classes.jar")]
    )

    shutil.copy(linked, APK)
    with zipfile.ZipFile(APK, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT / "dex" / "classes.dex", "classes.dex")
        for model in (ROOT / "onnx_micrographs").glob("*.onnx"):
            zf.write(model, f"assets/{model.name}")
        for lib in (OUT / "aar" / "jni" / "arm64-v8a").glob("*.so"):
            zf.write(lib, f"lib/arm64-v8a/{lib.name}")

    aligned = OUT / "aligned.apk"
    run([str(BUILD_TOOLS / "zipalign"), "-f", "-p", "4", str(APK), str(aligned)])

    if not KEYSTORE.exists():
        run(
            [
                "keytool",
                "-genkeypair",
                "-v",
                "-keystore",
                str(KEYSTORE),
                "-storepass",
                "android",
                "-keypass",
                "android",
                "-alias",
                "androiddebugkey",
                "-keyalg",
                "RSA",
                "-keysize",
                "2048",
                "-validity",
                "10000",
                "-dname",
                "CN=Android Debug,O=Android,C=US",
            ]
        )
    run(
        [
            str(BUILD_TOOLS / "apksigner"),
            "sign",
            "--ks",
            str(KEYSTORE),
            "--ks-pass",
            "pass:android",
            "--key-pass",
            "pass:android",
            "--out",
            str(SIGNED_APK),
            str(aligned),
        ]
    )
    run([str(BUILD_TOOLS / "apksigner"), "verify", "--verbose", str(SIGNED_APK)])
    print(SIGNED_APK)


if __name__ == "__main__":
    main()
