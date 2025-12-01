# Copyright (c) 2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: BSD-3-Clause
set(CMAKE_POLICY_DEFAULT_CMP0144 NEW)
cmake_minimum_required(VERSION 3.18 FATAL_ERROR)

project(pyhwloc LANGUAGES C VERSION 0.0.0)

list(APPEND CMAKE_MODULE_PATH "${pyhwloc_SOURCE_DIR}/cmake/")

option(PYHWLOC_FETCH_HWLOC "Fetch hwloc from GitHub instead of using system version" OFF)

set(PYHWLOC_BUILD_HWLOC_CMAKE OFF)
if(WIN32)
  set(PYHWLOC_BUILD_HWLOC_CMAKE ON)
endif()
message(STATUS "PYHWLOC_BUILD_HWLOC_CMAKE: ${PYHWLOC_BUILD_HWLOC_CMAKE}")

add_library(pyhwloc SHARED src/ext/pyhwloc.c)

set(PYHWLOC_OUTPUT_DIR ${pyhwloc_SOURCE_DIR}/src/pyhwloc/_lib/)

if(PYHWLOC_FETCH_HWLOC)
  set(PYHWLOC_CONFIG_HWLOC OFF CACHE BOOL "")

  include(FetchContent)
  file(READ ${pyhwloc_SOURCE_DIR}/dev/hwloc_version HWLOC_VERSION)
  FetchContent_Declare(
    hwloc
    GIT_REPOSITORY https://github.com/open-mpi/hwloc.git
    GIT_TAG        ${HWLOC_VERSION}
  )

  # Configure hwloc build options
  FetchContent_MakeAvailable(hwloc)
  if(NOT PYHWLOC_CONFIG_HWLOC)
    if(PYHWLOC_BUILD_HWLOC_CMAKE)
      execute_process(
        COMMAND
        cmake
        -S ${hwloc_SOURCE_DIR}/contrib/windows-cmake
        -B ${hwloc_BINARY_DIR}
        -G ${CMAKE_GENERATOR}
        -DCMAKE_INSTALL_PREFIX=${PYHWLOC_OUTPUT_DIR}
        -DBUILD_SHARED_LIBS=ON
        -DHWLOC_WITH_CUDA=ON
        -DHWLOC_ENABLE_PLUGINS=ON
        WORKING_DIRECTORY ${hwloc_SOURCE_DIR}
      )
    else()
      execute_process(
        COMMAND ${hwloc_SOURCE_DIR}/autogen.sh WORKING_DIRECTORY ${hwloc_SOURCE_DIR}
      )
      execute_process(
        COMMAND ${hwloc_SOURCE_DIR}/configure --enable-plugins --prefix=${PYHWLOC_OUTPUT_DIR}
        WORKING_DIRECTORY ${hwloc_BINARY_DIR}
      )
    endif()
    set(PYHWLOC_CONFIG_HWLOC ON CACHE BOOL "" FORCE)
  endif()

  include(ProcessorCount)
  ProcessorCount(nproc)

  # fixme; How to respect the --parallel option?
  if(PYHWLOC_BUILD_HWLOC_CMAKE)
    add_custom_command(
      OUTPUT ${PYHWLOC_OUTPUT_DIR}/bin/hwloc.dll
      COMMAND cmake --build ${hwloc_BINARY_DIR} --config=Release --parallel=${nproc} --target=install
      WORKING_DIRECTORY ${hwloc_BINARY_DIR}
    )
    add_custom_target(install_hwloc DEPENDS ${PYHWLOC_OUTPUT_DIR}/bin/hwloc.dll)

    set(HWLOC_LIBRARY ${PYHWLOC_OUTPUT_DIR}/lib/hwloc.lib)
    set(HWLOC_INCLUDE_DIR ${PYHWLOC_OUTPUT_DIR}/include/)
  else()
    add_custom_command(
      OUTPUT ${PYHWLOC_OUTPUT_DIR}/lib/libhwloc.so COMMAND make -j${nproc} install WORKING_DIRECTORY ${hwloc_BINARY_DIR}
    )
    add_custom_target(install_hwloc DEPENDS ${PYHWLOC_OUTPUT_DIR}/lib/libhwloc.so)
    set(HWLOC_LIBRARY ${PYHWLOC_OUTPUT_DIR}/lib/libhwloc.so)
    set(HWLOC_INCLUDE_DIR ${PYHWLOC_OUTPUT_DIR}/include/)
  endif()

  set(HWLOC_ROOT ${PYHWLOC_OUTPUT_DIR})
  set_target_properties(pyhwloc PROPERTIES
    # Do not add anything outside of the package
    INSTALL_RPATH_USE_LINK_PATH OFF
    # Do not add system toolchain path
    INSTALL_REMOVE_ENVIRONMENT_RPATH ON
    # Use relative path
    BUILD_RPATH_USE_ORIGIN ON)
else()
  find_package(hwloc REQUIRED)
endif()

message(STATUS "HWLOC_LIBRARY: ${HWLOC_LIBRARY}")
find_package(CUDAToolkit REQUIRED COMPONENTS nvml cuda_driver cudart_static)

target_link_libraries(pyhwloc PRIVATE ${HWLOC_LIBRARY})
target_include_directories(pyhwloc PRIVATE ${HWLOC_INCLUDE_DIR})
list(APPEND PYHWLOC_LIBS pyhwloc)

add_library(pyhwloc_cuda SHARED src/ext/cudr.c)
target_link_libraries(pyhwloc_cuda PRIVATE CUDA::cuda_driver ${HWLOC_LIBRARY})
target_include_directories(pyhwloc_cuda PRIVATE ${HWLOC_INCLUDE_DIR})
list(APPEND PYHWLOC_LIBS pyhwloc_cuda)

add_library(pyhwloc_cudart SHARED src/ext/cudart.c)
target_link_libraries(pyhwloc_cudart PRIVATE CUDA::cudart ${HWLOC_LIBRARY})
target_include_directories(pyhwloc_cudart PRIVATE ${HWLOC_INCLUDE_DIR})
list(APPEND PYHWLOC_LIBS pyhwloc_cudart)

add_library(pyhwloc_nvml SHARED src/ext/nvml.c)
target_link_libraries(pyhwloc_nvml PRIVATE CUDA::nvml ${HWLOC_LIBRARY})
target_include_directories(pyhwloc_nvml PRIVATE ${HWLOC_INCLUDE_DIR})
list(APPEND PYHWLOC_LIBS pyhwloc_nvml)

include(GenerateExportHeader)

foreach(lib IN LISTS PYHWLOC_LIBS)
  target_include_directories(${lib} PRIVATE ${pyhwloc_BINARY_DIR})
  # One header for each shared object as Windows distinguishes import and export.
  generate_export_header(${lib})
  if(PYHWLOC_FETCH_HWLOC)
    set_target_properties(${lib} PROPERTIES
      INSTALL_RPATH "$ORIGIN/lib"
      INSTALL_RPATH_USE_LINK_PATH OFF
      BUILD_RPATH_USE_ORIGIN ON)
    add_dependencies(${lib} install_hwloc)
  endif()
endforeach()

include(GNUInstallDirs)
install(TARGETS ${PYHWLOC_LIBS}
  ARCHIVE DESTINATION ${PYHWLOC_OUTPUT_DIR}
  LIBRARY DESTINATION ${PYHWLOC_OUTPUT_DIR}
  RUNTIME DESTINATION ${PYHWLOC_OUTPUT_DIR}
  INCLUDES DESTINATION ${PYHWLOC_OUTPUT_DIR}
)
