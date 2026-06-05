"""
VRoid VRM → TalkingHead-compatible GLB (fully automated)

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender \
        --background --python scripts/vroid_to_glb.py \
        -- path/to/avatar.vrm path/to/output.glb

Requires: VRM format extension installed in Blender (one-time GUI setup)
"""

import sys
import math
import bpy
from mathutils import Vector

# ── Parse args ────────────────────────────────────────────────────────────────

argv = sys.argv
try:
    sep = argv.index("--") + 1
except ValueError:
    print("Usage: blender --background --python vroid_to_glb.py -- <in.vrm> <out.glb>")
    sys.exit(1)

args = argv[sep:]
if len(args) < 2:
    print("ERROR: need <input.vrm> <output.glb>")
    sys.exit(1)

VRM_PATH = args[0]
GLB_PATH = args[1]
print(f"[vroid→glb] Input : {VRM_PATH}")
print(f"[vroid→glb] Output: {GLB_PATH}")


# ── 1. Clear default scene ────────────────────────────────────────────────────

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


# ── 2. Import VRM ─────────────────────────────────────────────────────────────

print("[vroid→glb] Importing VRM …")
try:
    bpy.ops.import_scene.vrm(filepath=VRM_PATH)
except AttributeError:
    print("ERROR: VRM format extension not installed in Blender.")
    print("  Open Blender → Edit → Preferences → Extensions → search 'VRM format' → Install")
    sys.exit(1)
print("[vroid→glb] VRM imported ✓")


# ── 3. Delete Colliders collection ────────────────────────────────────────────

to_delete = [col.name for col in bpy.data.collections if "Collider" in col.name or "collider" in col.name]
for name in to_delete:
    col = bpy.data.collections.get(name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)
        print(f"[vroid→glb] Deleted collection: {name}")


# ── 4. Rename VRoid bones → Mixamo/TalkingHead names ─────────────────────────

BONE_MAP = {
    # Spine
    "J_Bip_C_Hips": "Hips", "J_Bip_C_Spine": "Spine", "J_Bip_C_Chest": "Spine1",
    "J_Bip_C_UpperChest": "Spine2", "J_Bip_C_Neck": "Neck", "J_Bip_C_Head": "Head",
    # Eyes
    "J_Adj_L_FaceEye": "LeftEye", "J_Adj_R_FaceEye": "RightEye",
    # Left arm
    "J_Bip_L_Shoulder": "LeftShoulder", "J_Bip_L_UpperArm": "LeftArm",
    "J_Bip_L_LowerArm": "LeftForeArm", "J_Bip_L_Hand": "LeftHand",
    # Left hand fingers
    "J_Bip_L_Thumb1": "LeftHandThumb1", "J_Bip_L_Thumb2": "LeftHandThumb2",
    "J_Bip_L_Thumb3": "LeftHandThumb3", "J_Bip_L_Index1": "LeftHandIndex1",
    "J_Bip_L_Index2": "LeftHandIndex2", "J_Bip_L_Index3": "LeftHandIndex3",
    "J_Bip_L_Middle1": "LeftHandMiddle1", "J_Bip_L_Middle2": "LeftHandMiddle2",
    "J_Bip_L_Middle3": "LeftHandMiddle3", "J_Bip_L_Ring1": "LeftHandRing1",
    "J_Bip_L_Ring2": "LeftHandRing2", "J_Bip_L_Ring3": "LeftHandRing3",
    "J_Bip_L_Little1": "LeftHandPinky1", "J_Bip_L_Little2": "LeftHandPinky2",
    "J_Bip_L_Little3": "LeftHandPinky3",
    # Right arm
    "J_Bip_R_Shoulder": "RightShoulder", "J_Bip_R_UpperArm": "RightArm",
    "J_Bip_R_LowerArm": "RightForeArm", "J_Bip_R_Hand": "RightHand",
    # Right hand fingers
    "J_Bip_R_Thumb1": "RightHandThumb1", "J_Bip_R_Thumb2": "RightHandThumb2",
    "J_Bip_R_Thumb3": "RightHandThumb3", "J_Bip_R_Index1": "RightHandIndex1",
    "J_Bip_R_Index2": "RightHandIndex2", "J_Bip_R_Index3": "RightHandIndex3",
    "J_Bip_R_Middle1": "RightHandMiddle1", "J_Bip_R_Middle2": "RightHandMiddle2",
    "J_Bip_R_Middle3": "RightHandMiddle3", "J_Bip_R_Ring1": "RightHandRing1",
    "J_Bip_R_Ring2": "RightHandRing2", "J_Bip_R_Ring3": "RightHandRing3",
    "J_Bip_R_Little1": "RightHandPinky1", "J_Bip_R_Little2": "RightHandPinky2",
    "J_Bip_R_Little3": "RightHandPinky3",
    # Left leg
    "J_Bip_L_UpperLeg": "LeftUpLeg", "J_Bip_L_LowerLeg": "LeftLeg",
    "J_Bip_L_Foot": "LeftFoot", "J_Bip_L_ToeBase": "LeftToeBase",
    # Right leg
    "J_Bip_R_UpperLeg": "RightUpLeg", "J_Bip_R_LowerLeg": "RightLeg",
    "J_Bip_R_Foot": "RightFoot", "J_Bip_R_ToeBase": "RightToeBase",
}

arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if not arm:
    print("ERROR: No armature found after VRM import")
    sys.exit(1)

renamed = 0
for bone in arm.data.bones:
    if bone.name in BONE_MAP:
        bone.name = BONE_MAP[bone.name]
        renamed += 1
print(f"[vroid→glb] Renamed {renamed} bones ✓")

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
edit_bones = arm.data.edit_bones

hips = edit_bones.get('Hips')
root = edit_bones.get('Root')
if hips and root:
    hips.parent = None
    edit_bones.remove(root)
    print("[vroid→glb] Root bone removed, Hips is root ✓")
elif hips:
    hips.parent = None

# Re-orient feet bones
for side, foot, toes in [("Left", "LeftFoot", "LeftToeBase"), ("Right", "RightFoot", "RightToeBase")]:
    f = edit_bones.get(foot)
    t = edit_bones.get(toes)
    if f and t:
        f.tail = t.head

bpy.ops.object.mode_set(mode='OBJECT')


# ── 5. Build eye look shape keys ──────────────────────────────────────────────

ARMATURE_NAME = arm.name

def ensure_basis(mesh):
    if not mesh.data.shape_keys:
        mesh.shape_key_add(name="Basis", from_mix=False)
        return
    if "Basis" not in mesh.data.shape_keys.key_blocks:
        mesh.shape_key_add(name="Basis", from_mix=False)

def remove_shape_key(mesh, name):
    keys = mesh.data.shape_keys
    if not keys:
        return
    kb = keys.key_blocks.get(name)
    if kb:
        mesh.shape_key_remove(kb)

def reset_pose(arm_obj):
    for pbone in arm_obj.pose.bones:
        pbone.location = (0.0, 0.0, 0.0)
        pbone.rotation_mode = 'XYZ'
        pbone.rotation_euler = (0.0, 0.0, 0.0)
        pbone.scale = (1.0, 1.0, 1.0)

def set_bone_rotation(pbone, axis, degrees):
    radians = math.radians(degrees)
    pbone.rotation_mode = 'XYZ'
    pbone.rotation_euler = (0.0, 0.0, 0.0)
    if axis == "X":
        pbone.rotation_euler.x = radians
    elif axis == "Z":
        pbone.rotation_euler.z = radians

def save_armature_as_shape_key(mesh, shape_name):
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode='OBJECT')
    for mod in mesh.modifiers:
        if mod.type == 'ARMATURE' and mod.show_viewport:
            bpy.ops.object.modifier_apply_as_shapekey(modifier=mod.name, keep_modifier=True)
            mesh.data.shape_keys.key_blocks[-1].name = shape_name
            return
    raise RuntimeError(f"No active Armature modifier on {mesh.name}")

EYE_CONFIGS = [
    {"mesh": "Face", "bone": "LeftEye",  "side": "Left",  "rotations": {"Up": -5, "Down": 5, "In": 5, "Out": -9}},
    {"mesh": "Face", "bone": "RightEye", "side": "Right", "rotations": {"Up": -5, "Down": 5, "In": -5, "Out": 9}},
]

arm_obj = bpy.data.objects.get(ARMATURE_NAME)
for cfg in EYE_CONFIGS:
    face_mesh = bpy.data.objects.get(cfg["mesh"])
    if not face_mesh or cfg["bone"] not in arm_obj.pose.bones:
        print(f"[vroid→glb] Skipping eye bake for {cfg['side']} (mesh/bone not found)")
        continue
    ensure_basis(face_mesh)
    pbone = arm_obj.pose.bones[cfg["bone"]]
    for direction, angle in cfg["rotations"].items():
        shape_name = f"eyeLook{direction}{cfg['side']}"
        remove_shape_key(face_mesh, shape_name)
        reset_pose(arm_obj)
        axis = "X" if direction in ("Up", "Down") else "Z"
        set_bone_rotation(pbone, axis, angle)
        bpy.context.view_layer.update()
        save_armature_as_shape_key(face_mesh, shape_name)
    reset_pose(arm_obj)
print("[vroid→glb] Eye look shape keys built ✓")


# ── 6. Build ARKit + Oculus viseme shape keys ─────────────────────────────────

SHAPEKEYS = [
    {"name": "eyeBlinkLeft",    "mix": [{"name": "Fcl_EYE_Close_L", "value": 1.0}]},
    {"name": "eyeBlinkRight",   "mix": [{"name": "Fcl_EYE_Close_R", "value": 1.0}]},
    {"name": "eyeSquintLeft",   "mix": [{"name": "Fcl_EYE_Joy_L",   "value": 0.4}]},
    {"name": "eyeSquintRight",  "mix": [{"name": "Fcl_EYE_Joy_R",   "value": 0.4}]},
    {"name": "eyeWideLeft",     "mix": [{"name": "Fcl_EYE_Spread",  "value": 1.0, "side": "left"}]},
    {"name": "eyeWideRight",    "mix": [{"name": "Fcl_EYE_Spread",  "value": 1.0, "side": "right"}]},
    {"name": "jawForward",      "mix": []},
    {"name": "jawLeft",         "mix": []},
    {"name": "jawRight",        "mix": []},
    {"name": "jawOpen",         "mix": []},
    {"name": "mouthClose",      "mix": [{"name": "Fcl_MTH_Close",   "value": 1.0}]},
    {"name": "mouthFunnel",     "mix": [{"name": "Fcl_MTH_U",       "value": 1.0}]},
    {"name": "mouthPucker",     "mix": [{"name": "Fcl_MTH_U",       "value": 1.0}]},
    {"name": "mouthLeft",       "mix": [{"name": "Fcl_MTH_Large", "value": -0.5, "side": "left",  "falloff": 0.01},
                                        {"name": "Fcl_MTH_Large", "value":  0.5, "side": "right", "falloff": 0.01}]},
    {"name": "mouthRight",      "mix": [{"name": "Fcl_MTH_Large", "value":  0.5, "side": "left",  "falloff": 0.01},
                                        {"name": "Fcl_MTH_Large", "value": -0.5, "side": "right", "falloff": 0.01}]},
    {"name": "mouthSmileLeft",  "mix": [{"name": "Fcl_MTH_Fun",  "value": 1.4, "side": "left",  "falloff": 0.01}]},
    {"name": "mouthSmileRight", "mix": [{"name": "Fcl_MTH_Fun",  "value": 1.4, "side": "right", "falloff": 0.01}]},
    {"name": "mouthFrownLeft",  "mix": [{"name": "Fcl_MTH_Angry","value": 1.0, "side": "left",  "falloff": 0.01}]},
    {"name": "mouthFrownRight", "mix": [{"name": "Fcl_MTH_Angry","value": 1.0, "side": "right", "falloff": 0.01}]},
    {"name": "mouthDimpleLeft", "mix": [{"name": "Fcl_MTH_Fun",  "value": 1.4, "side": "left",  "falloff": 0.01}]},
    {"name": "mouthDimpleRight","mix": [{"name": "Fcl_MTH_Fun",  "value": 1.4, "side": "right", "falloff": 0.01}]},
    {"name": "mouthStretchLeft","mix": [{"name": "Fcl_MTH_Large","value": 1.0, "side": "left",  "falloff": 0.01}]},
    {"name": "mouthStretchRight","mix":[{"name": "Fcl_MTH_Large","value": 1.0, "side": "right", "falloff": 0.01}]},
    {"name": "mouthRollLower",  "mix": [{"name": "Fcl_MTH_Up",   "value": 0.5}]},
    {"name": "mouthRollUpper",  "mix": [{"name": "Fcl_MTH_Down", "value": 0.5}]},
    {"name": "mouthShrugLower", "mix": []},
    {"name": "mouthShrugUpper", "mix": []},
    {"name": "mouthPressLeft",  "mix": [{"name": "Fcl_MTH_Close","value": 1.0, "side": "left",  "falloff": 0.01}]},
    {"name": "mouthPressRight", "mix": [{"name": "Fcl_MTH_Close","value": 1.0, "side": "right", "falloff": 0.01}]},
    {"name": "mouthLowerDownLeft", "mix":[{"name":"Fcl_MTH_Joy","value":0.5,"side":"left","falloff":0.01}]},
    {"name": "mouthLowerDownRight","mix":[{"name":"Fcl_MTH_Joy","value":0.5,"side":"right","falloff":0.01}]},
    {"name": "mouthUpperUpLeft",   "mix": []},
    {"name": "mouthUpperUpRight",  "mix": []},
    {"name": "browDownLeft",    "mix": [{"name": "Fcl_BRW_Angry",    "value": 1.0, "side": "left"}]},
    {"name": "browDownRight",   "mix": [{"name": "Fcl_BRW_Angry",    "value": 1.0, "side": "right"}]},
    {"name": "browInnerUp",     "mix": [{"name": "Fcl_BRW_Sorrow",   "value": 0.5},
                                        {"name": "Fcl_BRW_Surprised","value": 0.5}]},
    {"name": "browOuterUpLeft", "mix": [{"name": "Fcl_BRW_Sorrow",   "value": -1.0, "side": "left"}]},
    {"name": "browOuterUpRight","mix": [{"name": "Fcl_BRW_Sorrow",   "value": -1.0, "side": "right"}]},
    {"name": "cheekPuff",       "mix": []},
    {"name": "cheekSquintLeft", "mix": []},
    {"name": "cheekSquintRight","mix": []},
    {"name": "noseSneerLeft",   "mix": []},
    {"name": "noseSneerRight",  "mix": []},
    {"name": "tongueOut",       "mix": []},
    # Oculus visemes
    {"name": "viseme_sil", "mix": []},
    {"name": "viseme_aa",  "mix": [{"name": "Fcl_MTH_A", "value": 1.0}]},
    {"name": "viseme_E",   "mix": [{"name": "Fcl_MTH_E", "value": 1.0}]},
    {"name": "viseme_I",   "mix": [{"name": "Fcl_MTH_I", "value": 1.0}]},
    {"name": "viseme_O",   "mix": [{"name": "Fcl_MTH_O", "value": 1.0}]},
    {"name": "viseme_U",   "mix": [{"name": "Fcl_MTH_U", "value": 1.0}]},
    {"name": "viseme_PP",  "mix": [{"name": "Fcl_MTH_Close", "value": 1.0}]},
    {"name": "viseme_FF",  "mix": [{"name": "Fcl_MTH_Close", "value": 0.3},
                                   {"name": "Fcl_MTH_I",     "value": 0.4},
                                   {"name": "Fcl_MTH_Up",    "value": 0.5}]},
    {"name": "viseme_TH",  "mix": [{"name": "Fcl_MTH_Small", "value": 0.5},
                                   {"name": "Fcl_MTH_A",     "value": 0.2},
                                   {"name": "Fcl_MTH_Down",  "value": 0.3}]},
    {"name": "viseme_DD",  "mix": [{"name": "Fcl_MTH_Small", "value": 0.4},
                                   {"name": "Fcl_MTH_E",     "value": 0.3},
                                   {"name": "Fcl_MTH_Down",  "value": 0.2}]},
    {"name": "viseme_kk",  "mix": [{"name": "Fcl_MTH_Small", "value": 0.3},
                                   {"name": "Fcl_MTH_A",     "value": 0.3},
                                   {"name": "Fcl_MTH_Down",  "value": 0.2}]},
    {"name": "viseme_CH",  "mix": [{"name": "Fcl_MTH_U",     "value": 0.5},
                                   {"name": "Fcl_MTH_Small", "value": 0.4}]},
    {"name": "viseme_SS",  "mix": [{"name": "Fcl_MTH_I",     "value": 0.6},
                                   {"name": "Fcl_MTH_Small", "value": 0.3}]},
    {"name": "viseme_nn",  "mix": [{"name": "Fcl_MTH_Small", "value": 0.4},
                                   {"name": "Fcl_MTH_E",     "value": 0.2},
                                   {"name": "Fcl_MTH_Close", "value": 0.2}]},
    {"name": "viseme_RR",  "mix": [{"name": "Fcl_MTH_O",     "value": 0.4},
                                   {"name": "Fcl_MTH_Small", "value": 0.3}]},
]

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)

def side_weight(x, side, falloff):
    if side is None:
        return 1.0
    if falloff <= 0:
        if side == "right":
            return 1.0 if x < 0 else 0.0
        elif side == "left":
            return 1.0 if x > 0 else 0.0
        return 1.0
    t = (x + falloff) / (2 * falloff)
    if side == "right":
        if x <= -falloff: return 1.0
        if x >= falloff:  return 0.0
        return 1.0 - smoothstep(t)
    elif side == "left":
        if x >= falloff:  return 1.0
        if x <= -falloff: return 0.0
        return smoothstep(t)
    return 1.0

def traverse(x):
    yield x
    if hasattr(x, 'children'):
        for c in x.children:
            yield from traverse(c)

def has_shapekeys(x):
    return hasattr(x, 'data') and hasattr(x.data, 'shape_keys') and hasattr(x.data.shape_keys, 'key_blocks')

for r in bpy.context.scene.objects:
    for o in traverse(r):
        if not has_shapekeys(o):
            continue
        keys = o.data.shape_keys.key_blocks
        basis = keys.get("Basis")
        if basis is None:
            continue
        for b in SHAPEKEYS:
            name = b["name"]
            mix = b["mix"]
            existing = keys.get(name)
            if existing is not None:
                o.shape_key_remove(existing)
            valid_mix = [m for m in mix if keys.get(m["name"]) is not None]
            if not valid_mix:
                if o.name == "Face":
                    new_key = o.shape_key_add(name=name, from_mix=True)
                    new_key.value = 0.0
                continue
            for k in keys:
                k.value = 0
            new_key = o.shape_key_add(name=name, from_mix=False)
            for i, v in enumerate(o.data.vertices):
                base_co = basis.data[i].co.copy()
                final_co = base_co.copy()
                for m in valid_mix:
                    src_key = keys.get(m["name"])
                    if src_key is None:
                        continue
                    weight  = m.get("value", 1.0)
                    side    = m.get("side", None)
                    falloff = m.get("falloff", 0)
                    w = side_weight(base_co.x, side, falloff)
                    if w <= 0.0:
                        continue
                    delta = src_key.data[i].co - base_co
                    final_co += delta * weight * w
                new_key.data[i].co = final_co
                new_key.value = 0.0

print("[vroid→glb] ARKit + Oculus shape keys built ✓")


# ── 7. Add bilateral combined shape keys (required by TalkingHead) ────────────
# TalkingHead drives animation via: eyesClosed, eyesLookDown, eyesLookUp,
# mouthSmile, mouthOpen — bilateral averages of left+right ARKit keys.

BILATERAL_KEYS = [
    ("eyesClosed",   [("eyeBlinkLeft", 0.5),  ("eyeBlinkRight", 0.5)]),
    ("eyesLookDown", [("eyeLookDownLeft", 0.5),("eyeLookDownRight", 0.5)]),
    ("eyesLookUp",   [("eyeLookUpLeft", 0.5),  ("eyeLookUpRight", 0.5)]),
    ("mouthSmile",   [("mouthSmileLeft", 0.5), ("mouthSmileRight", 0.5)]),
    ("mouthOpen",    [("jawOpen", 1.0)]),
]

for obj in bpy.data.objects:
    if obj.type != 'MESH' or not obj.data.shape_keys:
        continue
    keys = obj.data.shape_keys.key_blocks
    if "Basis" not in keys:
        continue
    basis = keys["Basis"]
    for new_name, sources in BILATERAL_KEYS:
        # remove existing
        if new_name in keys:
            obj.shape_key_remove(keys[new_name])
        valid = [(keys[src], w) for src, w in sources if src in keys]
        if not valid:
            continue
        # reset all key values
        for k in keys:
            k.value = 0.0
        new_key = obj.shape_key_add(name=new_name, from_mix=False)
        for i in range(len(obj.data.vertices)):
            base_co = basis.data[i].co.copy()
            final_co = base_co.copy()
            for src_key, weight in valid:
                final_co += (src_key.data[i].co - base_co) * weight
            new_key.data[i].co = final_co
        new_key.value = 0.0

print("[vroid→glb] Bilateral shape keys added ✓")


# ── 8. Fix bone axes (T-pose) ─────────────────────────────────────────────────

BONE_AXES_DATA_T = {
    "Head": [3.81044e-07, -0.990155, -0.139976], "HeadTop_End": [2.93097e-07, -0.999963, 0.00863087],
    "Hips": [-5.23035e-05, -0.998203, 0.0599285], "LeftArm": [0.00021426, 0.022599, -0.999745],
    "LeftFoot": [0.0541387, -0.600338, 0.797912], "LeftForeArm": [-0.0341937, 0.0119785, -0.999343],
    "LeftHand": [0.0907265, -0.16043, -0.982869],
    "LeftHandIndex1": [-0.0292601, -0.187298, -0.981867], "LeftHandIndex2": [-0.0339214, -0.121124, -0.992058],
    "LeftHandIndex3": [-0.0334821, -0.213779, -0.976308], "LeftHandIndex4": [0.091196, -0.124351, -0.988039],
    "LeftHandMiddle1": [-0.0301688, -0.174304, -0.98423], "LeftHandMiddle2": [-0.033935, -0.128504, -0.991128],
    "LeftHandMiddle3": [-0.0339587, -0.142883, -0.989157], "LeftHandMiddle4": [0.124358, -0.132995, -0.983284],
    "LeftHandPinky1": [-0.029454, -0.149489, -0.988325], "LeftHandPinky2": [-0.0339946, -0.0815342, -0.996091],
    "LeftHandPinky3": [-0.0338747, -0.15072, -0.987996], "LeftHandPinky4": [0.045214, -0.107585, -0.993167],
    "LeftHandRing1": [-0.0294886, -0.135611, -0.990323], "LeftHandRing2": [-0.034015, -0.0966198, -0.99474],
    "LeftHandRing3": [-0.0340394, -0.122593, -0.991873], "LeftHandRing4": [-0.00197432, -0.116866, -0.993146],
    "LeftHandThumb1": [-0.454559, 0.115889, -0.883145], "LeftHandThumb2": [-0.47989, 0.0847829, -0.873222],
    "LeftHandThumb3": [-0.477725, 0.0894662, -0.873942], "LeftHandThumb4": [-0.39936, 0.107931, -0.910419],
    "LeftLeg": [-0.0025901, -0.997624, -0.0688498], "LeftShoulder": [0.0955264, -0.0356792, -0.994787],
    "LeftToeBase": [0.0485404, 0.0274734, 0.998443], "LeftToe_End": [-0.999978, 0.00660707, 0.000249416],
    "LeftUpLeg": [-0.00191275, -0.999998, 0.000967459], "Neck": [2.55582e-07, -0.969599, -0.244701],
    "RightArm": [-0.000215599, 0.0225984, -0.999745],
    "RightFoot": [-0.0541308, -0.600241, 0.797985], "RightForeArm": [0.0341911, 0.0119773, -0.999344],
    "RightHand": [-0.0907132, -0.160435, -0.982869], "RightHandIndex1": [0.0292433, -0.187301, -0.981867],
    "RightHandIndex2": [0.0339327, -0.121103, -0.99206], "RightHandIndex3": [0.0334897, -0.213786, -0.976306],
    "RightHandIndex4": [-0.0911881, -0.124356, -0.988039], "RightHandMiddle1": [0.0301564, -0.174307, -0.984229],
    "RightHandMiddle2": [0.0338937, -0.128498, -0.99113], "RightHandMiddle3": [0.0339647, -0.142883, -0.989157],
    "RightHandMiddle4": [-0.124356, -0.132992, -0.983285], "RightHandPinky1": [0.0294101, -0.149479, -0.988327],
    "RightHandPinky2": [0.0339885, -0.0815093, -0.996093], "RightHandPinky3": [0.0339319, -0.150714, -0.987995],
    "RightHandPinky4": [-0.045171, -0.107558, -0.993172], "RightHandRing1": [0.0294796, -0.135614, -0.990323],
    "RightHandRing2": [0.034038, -0.0966193, -0.994739], "RightHandRing3": [0.0340057, -0.12257, -0.991877],
    "RightHandRing4": [0.00196401, -0.11687, -0.993145], "RightHandThumb1": [0.454551, 0.115871, -0.883152],
    "RightHandThumb2": [0.479888, 0.0847768, -0.873224], "RightHandThumb3": [0.477711, 0.0894437, -0.873952],
    "RightHandThumb4": [0.399355, 0.1079, -0.910425], "RightLeg": [0.00260206, -0.997627, -0.0687953],
    "RightShoulder": [-0.0955169, -0.0356809, -0.994788], "RightToeBase": [-0.0487178, 0.0275893, 0.998431],
    "RightToe_End": [0.99906, 0.00601406, 0.0429352], "RightUpLeg": [0.00192306, -0.999998, 0.00102428],
    "Spine": [3.02932e-07, -0.996171, 0.0874251], "Spine1": [4.99894e-07, -0.987185, 0.159582],
    "Spine2": [2.4899e-07, -0.999456, 0.0329908],
}

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
edit_bones = arm.data.edit_bones
applied = 0
for name, ref_z in BONE_AXES_DATA_T.items():
    if name in edit_bones:
        edit_bones[name].align_roll(Vector(ref_z))
        applied += 1
bpy.ops.object.mode_set(mode='OBJECT')
print(f"[vroid→glb] Bone axes fixed ({applied} bones) ✓")


# ── 8. Set Metallic = 0 for all materials ─────────────────────────────────────

for mat in bpy.data.materials:
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                node.inputs['Metallic'].default_value = 0.0
                # VRoid MToon → PBR 변환 시 색이 창백해지는 현상 보정.
                # Roughness를 낮추면 색이 더 선명하고 vivid하게 보임.
                node.inputs['Roughness'].default_value = 0.6
print("[vroid→glb] Metallic=0, Roughness=0.6 applied ✓")


# ── 9. Shade Smooth (per-vertex normals → 폴리곤 경계선 제거) ─────────────────

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.shade_smooth()
print("[vroid→glb] Shade smooth applied ✓")


# ── 9. Apply All Transforms ───────────────────────────────────────────────────

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
print("[vroid→glb] All transforms applied ✓")


# ── 10. Export GLB ────────────────────────────────────────────────────────────

bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format='GLB',
    export_animations=False,
    export_yup=True,
)
print(f"[vroid→glb] Exported: {GLB_PATH} ✓")
