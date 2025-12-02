目录/文件,描述,关键依赖
main.py,程序的入口文件，负责初始化 QApplication 和主窗口。,widgets/main_window.py
ui_utils.py **UI继承**BaseTabWidget 为所有 Tab 提供了统一的 UI 加载机制，简化了 widgets/ 目录下文件的代码。

data/,数据存储目录。,
├── classified_data.json,已分类的文本记录。,
└── custom_keywords.json,用户自定义的关键词。,

resources/，界面图片


services/,核心业务逻辑层。 包含所有数据处理、分析算法功能。
├── analysis_service.py,核心服务类 (QingShiluService)。 【文本处理的核心文件】负责分析、推荐算法。
针对文件中的每一条独立的文本记录，都调用一次 run_full_analysis(original_text)
├── constants.py,存储 JSON 文件路径、配置等常量。,N/A
├── data_model.py,数据管理类 (DataModel)。 负责加载/保存数据，管理关键词和分类数据。
_get_default_category_structure可直接修改代码进行分类管理（后续也可以独立出来）
├── 
├── file_manager.py，FileManager 类：文件I/O、《批量处理》、UI交互
└──  keywords_data.py：关键词库，用来存储关键词，减少data_model的代码体积


├── ui/	UI 文件目录。 (被 ui_utils.py 依赖)，不涉及功能实现，静态声明	
├── batch_tab.ui	BatchTabWidget 的 UI 文件。	
├── category_tab.ui	分类管理页窗口 。
├── keyword_tab.ui	关键词管理窗口 。
├── main_window.ui	主窗口外壳。	
├── single_tab.ui	SingleTabWidget 的 UI 文件。	
└── stats_tab.ui	统计查看页窗口

widgets/,《用户界面组件层功能》 包含所有 Qt Widget 类，用于加载UI，UI显示功能。动态实现：可以动态修改一些ui样式
├── __init__.py,（保持为空，标记为 Python 包）,N/A
├── batch_tab.py,批量文件处理界面。,analysis_service.py
├── category_dialog.py,分类管理界面。,analysis_service.py
├── keyword_tab.py,关键词管理界面。,analysis_service.py
├── single_tab.py,单条文本处理界面。,analysis_service.py
└── stats_tab.py,统计查看界面。,analysis_service.py

