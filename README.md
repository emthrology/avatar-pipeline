# avatar-pipeline

VRoid Studio(.vrm) 아바타를 [TalkingHead.js](https://github.com/met4citizen/TalkingHead) 호환 GLB로 변환하는 파이프라인.

## 변환 결과물 요구사항

| 조건 | 내용 |
|------|------|
| 리그 | Mixamo Humanoid 호환 |
| ARKit blendshape | 52개 (camelCase) |
| Oculus viseme | 15개 (`viseme_*` 접두사) |
| 양측성 키 | `eyesClosed`, `eyesLookDown`, `eyesLookUp`, `mouthSmile`, `mouthOpen` |
| 압축 | Draco / meshopt 비활성화 |
| 포맷 | GLB |

## 환경

- Python 3.10+
- Blender 5.1.2 (`/Applications/Blender.app/Contents/MacOS/Blender`)
- Blender에 **VRM format 확장** 설치 필요 (1회 GUI 설치): Edit → Preferences → Extensions → "VRM format"

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 사용법

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background --python scripts/vroid_to_glb.py \
  -- input/your_avatar.vrm output/your_avatar.glb
```

**VRoid Studio export 주의사항:**
- 파일 크기 9MB 이하 목표 → Reduce Polygons 활성화 필수
- 15MB 이상이면 Three.js 렌더링 프레임 드랍 발생

## 검증

```bash
source .venv/bin/activate && python3 -c "
from pygltflib import GLTF2
g = GLTF2().load('output/your_avatar.glb')
for m in g.meshes:
    for prim in m.primitives:
        if prim.targets and m.extras:
            names = m.extras.get('targetNames', [])
            arkit     = [n for n in names if n[0].islower() and not n.startswith('viseme_')]
            viseme    = [n for n in names if n.startswith('viseme_')]
            bilateral = [n for n in names if n in ('eyesClosed','eyesLookDown','eyesLookUp','mouthSmile','mouthOpen')]
            print('ARKit:', len(arkit), '/ viseme:', len(viseme), '/ bilateral:', len(bilateral))
"
```

기대 출력: `ARKit: 52+ / viseme: 15 / bilateral: 5`

## 파이프라인 처리 단계

`scripts/vroid_to_glb.py`가 수행하는 작업:

1. VRM import
2. Collider 오브젝트 삭제
3. 본 이름 변환 (VRoid `J_Bip_*` → Mixamo)
4. Root 본 제거, Hips를 루트로 설정
5. 눈 움직임 shape key 생성 (`eyeLookUp/Down/In/Out`)
6. ARKit 52 + Oculus viseme 15 shape key 생성
7. 양측성 키 생성 (`eyesClosed` 등 5종)
8. Bone axes 수정 (T-pose 기준)
9. Metallic=0, Roughness=0.6 적용
10. Shade Smooth 적용
11. GLB export (압축 비활성화)
