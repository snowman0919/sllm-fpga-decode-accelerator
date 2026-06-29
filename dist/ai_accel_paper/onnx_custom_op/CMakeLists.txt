cmake_minimum_required(VERSION 3.20)
project(fpga_matvec_custom_op LANGUAGES CXX)

add_library(fpga_matvec_custom_op SHARED fpga_matvec_custom_op.cpp)
target_compile_features(fpga_matvec_custom_op PRIVATE cxx_std_17)

if(NOT DEFINED ONNXRUNTIME_ROOT)
  message(WARNING "ONNXRUNTIME_ROOT is not set; this target is a build scaffold.")
else()
  target_include_directories(fpga_matvec_custom_op PRIVATE "${ONNXRUNTIME_ROOT}/include")
  target_link_directories(fpga_matvec_custom_op PRIVATE "${ONNXRUNTIME_ROOT}/lib")
endif()
