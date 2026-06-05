# CLAUDE.md — avatar-pipeline

game-avatar-companion 프로젝트에서 사용할 GLB 아바타를 제작하는 변환 파이프라인.
TalkingHead.js가 요구하는 ARKit 52 + Oculus 15 + Mixamo 리그 포맷으로 아바타를 변환한다.

## 현재 주력 파이프라인: VRoid VRM → GLB

```
VRoid Studio (.vrm export)
    └─ vroid_to_glb.py (Blender 헤드리스)
          ├─ Colliders 삭제
          ├─ 본 이름 변환 (VRoid J_Bip_* → Mixamo)
          ├─ Root 본 제거
          ├─ 눈 움직임 shape key 생성
          ├─ ARKit 52 + Oculus viseme 15 생성
          ├─ 양측성 키 생성 (eyesClosed, mouthSmile 등)
          ├─ Bone axes 수정 (T-pose)
          ├─ Metallic=0, Roughness=0.6
          ├─ Shade Smooth 적용
          └─ GLB export
    → ../game-avatar-companion/public/avatars/
```

## TalkingHead.js 아바타 요구사항

| 조건             | 내용                                                                                                        |
| ---------------- | ----------------------------------------------------------------------------------------------------------- |
| 리그             | Mixamo Humanoid 호환                                                                                        |
| ARKit blendshape | 52개 (camelCase 이름)                                                                                       |
| Oculus viseme    | 15개 (`viseme_*` 접두사)                                                                                    |
| 양측성 키        | eyesClosed / eyesLookDown / eyesLookUp / mouthSmile / mouthOpen — **없으면 `eyeBlinkLeft.limit TypeError`** |
| 압축             | meshopt / Draco 압축 불가 (TalkingHead @1.3 미지원)                                                         |
| 포맷             | GLB (GLTF 바이너리)                                                                                         |

## 환경 설정

- Python 3.10.14
- Blender 5.1.2 (`/Applications/Blender.app/Contents/MacOS/Blender`)
- Blender에 **VRM format 확장** 설치 필요 (1회 GUI 설치): Edit → Preferences → Extensions → "VRM format"
- venv는 avatar-pipeline 로컬에만 존재 (Python 스크립트용 pygltflib 등)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 사용법

```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background --python scripts/vroid_to_glb.py \
  -- path/to/avatar.vrm ../game-avatar-companion/public/avatars/output.glb
```

**VRoid Studio export 주의사항:**

- 파일 크기 9MB 이하가 목표 → **Reduce Polygons(폴리곤 감소)** 활성화 필수
- 15MB 이상이면 Three.js 렌더링 프레임 드랍 발생

## 양측성 키 (Bilateral Keys)

TalkingHead이 idle 애니메이션 구동에 필수로 사용하는 combined shape key.
없으면 `eyeBlinkLeft.limit TypeError` 발생.

```python
BILATERAL_KEYS = [
    ("eyesClosed",   [("eyeBlinkLeft", 0.5),   ("eyeBlinkRight", 0.5)]),
    ("eyesLookDown", [("eyeLookDownLeft", 0.5), ("eyeLookDownRight", 0.5)]),
    ("eyesLookUp",   [("eyeLookUpLeft", 0.5),   ("eyeLookUpRight", 0.5)]),
    ("mouthSmile",   [("mouthSmileLeft", 0.5),  ("mouthSmileRight", 0.5)]),
    ("mouthOpen",    [("jawOpen", 1.0)]),
]
```

## 변환된 아바타 목록

| 파일                  | 소스 VRM           | 크기   | 비고                                   |
| --------------------- | ------------------ | ------ | -------------------------------------- |
| `sample-b.glb`        | sample_b.vrm       | ~7.7MB | ✅                                     |
| `sample-c.glb`        | sample_c.vrm       | ~7.7MB | ✅                                     |
| `sample-d.glb`        | sample_d.vrm       | ~7.7MB | ✅                                     |
| `vroid-custom.glb`    | my_avatar.vrm      | ~15MB  | 폴리곤 감소 전 변환 → 프레임 드랍 가능 |
| `avatar-sample-m.glb` | AvatarSample_M.vrm | ~9.3MB | ✅                                     |

## 검증 방법

```bash
source .venv/bin/activate && python3 -c "
from pygltflib import GLTF2
g = GLTF2().load('path/to/output.glb')
for m in g.meshes:
    for prim in m.primitives:
        if prim.targets and m.extras:
            names = m.extras.get('targetNames', [])
            arkit  = [n for n in names if n[0].islower() and not n.startswith('viseme_')]
            viseme = [n for n in names if n.startswith('viseme_')]
            bilateral = [n for n in names if n in ('eyesClosed','eyesLookDown','eyesLookUp','mouthSmile','mouthOpen')]
            print('ARKit:', len(arkit), '/ viseme:', len(viseme), '/ bilateral:', len(bilateral))
"
```

기대 출력: `ARKit: 52+ / viseme: 15 / bilateral: 5`

## 디렉토리 구조

```
avatar-pipeline/
├── .venv/                        # 가상환경 (gitignore)
├── scripts/
│   ├── vroid_to_glb.py           # ★ 현재 주력 파이프라인 (VRM→GLB)
│   ├── fbx_to_talkinghead.py     # 구버전 — RocketBox FBX용 (사용 중단)
│   ├── fbx_to_glb.py             # 구버전 — 단순 FBX→GLB (사용 중단)
│   ├── build-vroid-eyes.py       # 눈 shape key 생성 단독 스크립트 (파이프라인에 통합됨)
│   ├── build-vroid-shapekeys.py  # ARKit shape key 생성 단독 스크립트 (파이프라인에 통합됨)
│   ├── rename-vroid-bones.py     # 본 이름 변환 단독 스크립트 (파이프라인에 통합됨)
│   └── ...                       # 기타 실험용 스크립트
├── arkit-blendshape-tool/        # 클론됨 — 다른 소스 아바타(Mixamo 등) 변환 시 예비
├── input/                        # 원본 VRM 파일
├── output/                       # 변환된 GLB (임시 보관)
├── reference/                    # brunette.glb 등 참고 아바타
├── requirements.txt
└── .gitignore
```

## 작업 상태

- [x] 파이프라인 구조 설계
- [x] Blender VRM 확장 설치 및 headless 변환 확인
- [x] 본 이름 변환 (VRoid J*Bip*\* → Mixamo)
- [x] ARKit 52 + Oculus viseme 15 shape key 생성
- [x] 양측성 키 생성 (eyesClosed 등 5종)
- [x] Shade Smooth 적용 (폴리곤 경계선 제거)
- [x] sample-b, sample-c, sample-d, vroid-custom, avatar-sample-m 변환 완료
- [x] MeshToonMaterial 렌더링 (game-avatar-companion AvatarOverlay.tsx 에서 적용)
- [ ] B방식: 서버 사이드 VRM 업로드 → 자동 변환 파이프라인 (Cloud Run + Blender Docker)

## 과거 시도 (중단)

### Microsoft RocketBox (FBX)

- 중단 이유: `_facial.fbx`는 두부 메시만 포함 → 전신 아바타 불가
- 스크립트: `fbx_to_talkinghead.py` (보존, 사용 중단)

### Avaturn T2

- 중단 이유: ARKit 52 포함 플랜이 유료 전용
