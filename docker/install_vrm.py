"""
Blender headless 에서 VRM format 확장을 설치하는 스크립트.
Dockerfile RUN 단계에서 1회 실행.
"""
import bpy

bpy.ops.preferences.addon_install(
    filepath='/tmp/vrm_addon.zip',
    overwrite=True
)
bpy.ops.preferences.addon_enable(module='VRM_Addon_for_Blender-release')
bpy.ops.wm.save_userpref()
print("[install_vrm] VRM addon installed and enabled.")
