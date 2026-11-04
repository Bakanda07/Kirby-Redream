# ssbu_glslang.dll

The Vulkan renderer's shader compiler: GLSL to SPIR-V. Built by `runtime/build_glslang.bat` from `runtime/vk_glslang_shim.c` and the
release libraries of [glslang](https://github.com/KhronosGroup/glslang) 16.6.0, whose license is in that repository's `LICENSE.txt`.

It is kept here so that a player's build needs no second toolchain. To make it again, run `runtime\build_glslang.bat` with
`GLSLANG_ROOT` set to the glslang release folder, then copy the result here.
