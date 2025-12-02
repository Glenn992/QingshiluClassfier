这是一个非常明智的决定。在开始大规模重构之前，将修改点和影响范围记录下来是最佳实践。

下面是对**“引入分类 ID 机制”**以解耦分类名称和关键词的完整总结和存档清单。

---

## 🌟 存档清单：引入分类 ID 机制（解耦分类名称与关键词）

**目标：** 将底层数据（关键词、已保存记录）的键从可变的分类名称字符串（`L1-L2-L3`）改为稳定的、不可变的 **分类 ID**。

### 影响模块概览

| 模块 | 修改类型 | 核心变更点 |
| :--- | :--- | :--- |
| **`services/category_structure.py`** | **数据结构变动** | 将分类结构重写为基于 ID 的映射表。 |
| **`services/keywords_data.py`** | **数据内容变动** | 将所有分类键从名称字符串改为 **ID**。 |
| **`services/data_model.py`** | **逻辑变动（核心）** | 新增 ID <-> 名称 的双向映射表，并提供转换方法。 |
| **`services/analysis_service.py`** | **逻辑变动** | 关键词匹配和推荐过程从操作名称改为操作 **ID**。 |
| **`widgets/*.py` (所有 Tab)** | **业务逻辑变动** | 所有显示和保存分类的地方都必须使用 `DataModel` 的转换方法。 |

---

### 详细操作步骤清单

#### 1. 数据配置层修改 (Category & Keyword Files)

| 文件 | 步骤 | 详细说明 |
| :--- | :--- | :--- |
| **`category_structure.py`** | **1. 引入 ID 映射** | 废弃原有的嵌套字典结构，改为一个新的全局变量（如 `CATEGORY_ID_MAP`），其中键是唯一的 ID（如 `"001"`），值是包含 `L1/L2/L3` 名称的列表或字典。 |
| **`keywords_data.py`** | **2. 键名替换** | 将 `QING_SHILU_KEYWORDS` 字典中的所有键名（例如 `"事务类-赈灾与民生保障-赈灾"`）替换为其对应的 **ID**（例如 `"001"`）。 |

#### 2. 服务层核心逻辑修改 (DataModel)

| 文件 | 步骤 | 详细说明 |
| :--- | :--- | :--- |
| **`data_model.py`** | **3. 构建双向映射** | 在 `DataModel.__init__` 或单独的私有方法中，基于新的 `CATEGORY_ID_MAP` 构建两个内部属性：`self._id_to_name_path_map` (ID -> 'L1/L2/L3' 路径) 和 `self._name_path_to_id_map` ('L1/L2/L3' 路径 -> ID)。 |
| **`data_model.py`** | **4. 新增转换 API** | 增加公共方法，供 Service 和 UI 调用：`get_id_from_name(name_path)` 和 `get_name_from_id(id)`。 |
| **`data_model.py`** | **5. 调整数据 I/O** | `save_classified_text`：接受分类 **ID** 并将其保存到 JSON 文件。`load_all_data`：从 JSON 文件中加载分类 **ID**。 |

#### 3. 业务逻辑层修改 (AnalysisService)

| 文件 | 步骤 | 详细说明 |
| :--- | :--- | :--- |
| **`analysis_service.py`** | **6. 调整推荐过程** | `_get_classification_recommendations` 方法现在直接使用 **ID** 作为 `category_scores` 的键进行计数和排序，最终返回推荐 **ID** 的列表。 |

#### 4. UI 层修改 (Widgets)

| 文件 | 步骤 | 详细说明 |
| :--- | :--- | :--- |
| **`widgets/*.py`** | **7. 显示逻辑调整** | 在加载历史记录、显示推荐结果或构建分类下拉框时，不再直接使用原始名称。需要调用 `self.service.model.get_name_from_id(id)` 将 ID 转换为可读的 L1/L2/L3 名称进行显示。 |
| **`widgets/*.py`** | **8. 保存逻辑调整** | 在用户手动点击或确认保存分类时，必须先调用 `self.service.model.get_id_from_name(name_path)` 将用户选择的名称路径转换为 **ID**，然后将该 ID 传递给 `save_classification_result` 方法。 |

---

这个 ID 机制将是您的项目实现最高可维护性的关键一步！请将此清单存档。