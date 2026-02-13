# Blender 模型导出指南

为了让 Nakari 桌宠正确显示你的 Blender 模型，请按照以下步骤导出：

## 一、模型准备

### 1. 创建 Morph Targets（形状键）

在 Blender 中为角色添加表情：

1. **进入编辑模式**，选择基础网格
2. **添加形状键**：
   - 在"形状键"面板中，点击 `+` 添加新形状键
   - 命名为：`happy`, `sad`, `surprised`, `thinking`, `angry`

3. **雕刻表情**：
   - 选择每个形状键
   - 进入编辑模式，移动顶点创建表情

4. **嘴部形状键**：
   - 添加 `mouth_open` 和 `mouth_close`
   - 用于说话时的嘴型动画

### 2. 表情参考

| 表情 | 顶点调整建议 |
|------|--------------|
| **happy** | 嘴角上扬，眉毛舒展 |
| **sad** | 嘴角下垂，眉毛内八字 |
| **surprised** | 嘴部张开呈 O 形，眉毛上扬 |
| **thinking** | 眼睛微眯，头部稍倾斜 |
| **angry** | 眉毛下压，嘴部呈直线 |

## 二、导出设置

### glTF 2.0 导出选项

1. **文件 → 导出 → glTF 2.0 (.glb/.gltf)**
2. **必选选项**：
   ```
   ✅ Include → Mesh
   ✅ Include → Morph Targets (形状键)
   ✅ Include → Materials
   ```

3. **推荐设置**：
   ```
   Format:           glTF Binary (.glb)
   Mesh:           ✓ Compression enabled
   Materials:        ✓ PBR Metal/Rough workflow
   ```
4. **点击"导出 glTF 2.0"**

## 三、Python 代码中的索引映射

导出后，需要在 Python 代码中映射形状键索引：

```python
# modeling/desktop_pet.py 中的配置
MORPH_TARGETS = {
    'neutral': 0,      # 基础表情（无变形）
    'happy': 1,        # 对应 Blender 中的 "happy" 形状键
    'sad': 2,          # 对应 "sad"
    'surprised': 3,     # 对应 "surprised"
    'thinking': 4,       # 对应 "thinking"
    'angry': 5,         # 对应 "angry"
    'mouth_open': 10,    # 对应 "mouth_open"
    'mouth_close': 11,   # 对应 "mouth_close"
}
```

**重要**：导出后，形状键的顺序可能与 Blender 中不同。
使用以下代码验证索引：

```python
# 测试代码 - 打印所有 morph targets
import trimesh
scene = trimesh.load('your_model.glb')
mesh = scene.geometry[list(scene.geometry.keys())[0]]

if hasattr(mesh, 'morph'):
    for i, name in enumerate(mesh.morph.keys()):
        print(f"Morph {i}: {name}")
```

## 四、完整工作流程

```
Blender          →  导出 glTF 2.0 (.glb)
                      ↓
Python 加载      →  trimesh/GL 渲染
                      ↓
桌面悬浮窗      →  显示 + 表情动画
```

## 五、常见问题

### Q: 表情不生效？
**A:** 检查 glTF 导出时是否勾选了 "Include → Morph Targets"

### Q: 模型位置不对？
**A:** 在 Blender 中将模型原点设置在角色底部中心：
- 选中所有网格
- 右键 → "设置原点" → "原点到质心"

### Q: 材质丢失？
**A:** 确保 Blender 材质使用 PBR 工作流，导出时包含纹理图片

## 六、快速测试模型

```bash
# 安装依赖
pip install trimesh pyglet PyQt5

# 测试加载模型
python -c "
import trimesh
scene = trimesh.load('models/your_model.glb')
print(f'Vertices: {len(scene.geometry)}')
print(f'Morph targets: {list(scene.geometry.values())[0].morph if hasattr(list(scene.geometry.values())[0], \"morph\") else \"None\"} ')
"
```

## 七、示例 Blender 项目结构

```
nakari_character.blend
├── Collection
│   ├── Body (mesh)
│   ├── Head (mesh)
│   ├── Eyes (mesh)
│   └── Mouth (mesh)
├── Armature (骨骼 - 可选)
└── Shape Keys
    ├── Basis (基础)
    ├── happy
    ├── sad
    ├── surprised
    ├── thinking
    ├── mouth_open
    └── mouth_close
```

导出时选择整个 Collection 或选择所有网格对象。
