# services-未拆分.py
# 核心业务逻辑层：包含数据模型、持久化、分析算法

import time
import json
# 【修正】导入 PySide6 UI 控件，因为 FileManager 依赖它们处理文件对话框
from PySide6.QtWidgets import QFileDialog, QWidget

# --- 数据持久化文件定义 ---
# 假设数据文件都保存在脚本运行目录下
CLASSIFIED_DATA_FILE = "../classified_data.json"
CUSTOM_KEYWORD_FILE = "../custom_keywords.json"
HISTORY_FILE = "translation_history.json"


class DataModel:
    """
    负责管理和持久化应用的所有数据：分类结构、关键词、历史记录。
    取代了 JS 中的 localStorage 机制。
    """

    def __init__(self):
        self.classifiedData = {}
        self.translationHistory = []
        self.customKeywordMap = {}
        self.categoryStructure = self._get_default_category_structure()
        self.qingShiluKeywords = self._get_qing_shilu_keywords()
        self.mergedKeywordMap = {}

        self.load_all_data()

    def _get_qing_shilu_keywords(self):
        # 完整的《清实录》专属词库（直接从 JS 翻译成 Python 字典）
        return {
            "事务类-赈灾与民生保障-赈灾": {
                "keywords": ["抚恤", "被灾", "赈济", "借籽种", "修费银", "淹毙", "旱", "雹", "霜", "饥", "贫民", "蠲免",
                             "救荒", "急赈", "赈粜", "平粜", "开仓", "发粟", "煮粥", "施粥"],
                "description": "灾害救济相关事务"
            },
            "事务类-赈灾与民生保障-救灾": {
                "keywords": ["抢险", "转移", "救援", "救护", "急赈", "堵口", "筑堤", "防汛", "抢险", "救灾"],
                "description": "灾害中的救援行动"
            },
            "事务类-赈灾与民生保障-民生工程": {
                "keywords": ["水利", "河道", "堤坝", "桥梁", "道路", "粮仓", "工程", "开工", "竣工", "漕运", "运河",
                             "闸坝", "涵洞", "圩田", "围垦"],
                "description": "改善民生的公共工程建设"
            },
            "事务类-官场与宫廷生活-信息交流": {
                "keywords": ["奏报", "题参", "疏报", "谕令", "批复", "公文", "往来", "题本", "奏折", "揭帖", "咨文",
                             "移文"],
                "description": "官场公文往来和信息传递"
            },
            "事务类-官场与宫廷生活-皇帝起居": {
                "keywords": ["起居", "礼仪", "祭祀", "典礼", "朝贺", "请安", "谒陵", "巡幸", "大阅", "耕耤", "亲蚕"],
                "description": "皇帝日常活动和宫廷礼仪"
            },
            "事务类-社会治安与司法-案件": {
                "keywords": ["审理", "判决", "断案", "审明", "结案", "案卷", "审拟", "覆审", "勘验", "检验"],
                "description": "各类司法案件的审理过程"
            },
            "事务类-社会治安与司法-刑事": {
                "keywords": ["盗窃", "杀人", "抢劫", "奸淫", "斗殴", "命案", "盗贼", "强盗", "土匪", "凶犯", "罪人",
                             "逃犯"],
                "description": "刑事案件及刑罚规定"
            },
            "事务类-社会治安与司法-走私": {
                "keywords": ["私盐", "走私", "违禁", "偷运", "漏税", "私茶", "私铸", "私贩", "夹带"],
                "description": "违禁物品走私及打击措施"
            },
            "事务类-社会治安与司法-流民": {
                "keywords": ["流民", "流亡", "逃荒", "迁徙", "安置", "招徕", "归籍", "土著", "客民"],
                "description": "流民管理和安置政策"
            },
            "事务类-社会治安与司法-社会秩序": {
                "keywords": ["保甲", "治安", "缉捕", "巡防", "保正", "甲长", "团练", "乡勇", "练总", "捕役"],
                "description": "维护地方稳定的社会管理措施"
            },
            "事务类-宗教与社会风俗-民间风俗": {
                "keywords": ["节日", "婚嫁", "丧葬", "习俗", "风俗", "节庆", "庙会", "赛会", "社火", "祈雨"],
                "description": "民间传统节日和风俗习惯"
            },
            "事务类-宗教与社会风俗-邪教和秘密宗教": {
                "keywords": ["邪教", "白莲教", "天理教", "秘密宗教", "禁教", "镇压", "罗教", "无为教", "闻香教"],
                "description": "被朝廷认定为邪教的组织及镇压措施"
            },
            "事务类-军事与外交事务-战争": {
                "keywords": ["进剿", "征讨", "攻城", "捷报", "凯旋", "投降", "战事", "军饷", "营制", "兵制", "练军",
                             "防军"],
                "description": "主动征战和防御作战等军事行动"
            },
            "事务类-军事与外交事务-边防": {
                "keywords": ["边防", "驻军", "边疆", "边境", "戍边", "卡伦", "台站", "军台", "驿站", "塘汛"],
                "description": "边疆防御和边境管理事务"
            },
            "事务类-军事与外交事务-外交往来": {
                "keywords": ["朝贡", "册封", "贡品", "使节", "藩属", "外国", "属国", "进贡", "回赐"],
                "description": "与藩属国和外国的使节往来"
            },
            "事务类-财政与经济事务-财政内容": {
                "keywords": ["钱粮", "赋税", "税收", "国库", "收支", "银两", "钱", "地丁", "漕粮", "盐课", "关税",
                             "厘金"],
                "description": "财政收支和赋税征收相关事务"
            },
            "事务类-财政与经济事务-商业贸易": {
                "keywords": ["贸易", "市场", "商税", "买卖", "交易", "商业", "行商", "坐商", "牙行", "铺户"],
                "description": "商品交易和市场管理事务"
            },
            "事务类-财政与经济事务-经济政策": {
                "keywords": ["专卖", "货币", "盐政", "铁政", "钱法", "改革", "币制", "银本位", "铜钱", "制钱"],
                "description": "影响经济的制度和政策"
            },
            "事务类-科举与教育-科举": {
                "keywords": ["科举", "进士", "举人", "秀才", "考试", "录取", "考官", "乡试", "会试", "殿试", "童试",
                             "生员"],
                "description": "科举考试流程和录取规则"
            },
            "问题类-不确定-待补充": {
                "keywords": ["不确定", "待考", "待查", "存疑", "未详", "俟查"],
                "description": "暂时无法明确归类的问题内容"
            },
            "问题类-行政失职-待补充": {
                "keywords": ["不效力", "徇私", "情面", "昏聩", "疏忽", "拖延", "不力", "玩忽", "贻误", "废弛"],
                "description": "官员行政失职的具体表现"
            },
            "问题类-腐败-待补充": {
                "keywords": ["贪污", "受贿", "侵吞", "克扣", "冒领", "虚报", "贿赂", "勒索", "敲诈", "舞弊"],
                "description": "官员贪腐行为"
            }
        }

    def _get_default_category_structure(self):
        # 默认分类结构（简化了描述以保持代码简洁，与 JS 基本一致）
        return {
            "0": {  # 事务类
                "赈灾与民生保障": {
                    "赈灾": "灾害发生后的赈济措施",
                    "救灾": "灾害中的救援行动",
                    "民生工程": "改善民生的公共工程"
                },
                "官场与宫廷生活": {
                    "信息交流": "官场公文往来、信息传递",
                    "皇帝起居": "皇帝的日常活动、宫廷礼仪"
                },
                "社会治安与司法": {
                    "案件": "各类司法案件的审理、判决",
                    "刑事": "刑事案件及刑罚规定",
                    "走私": "违禁物品走私及打击措施",
                    "流民": "流民管理、安置政策",
                    "社会秩序": "维护地方稳定的措施"
                },
                "宗教与社会风俗": {
                    "民间风俗": "民间节日、婚丧嫁娶等习俗",
                    "邪教和秘密宗教": "被朝廷认定为邪教的组织及镇压措施"
                },
                "军事与外交事务": {
                    "战争": "主动征战、防御作战等军事行动",
                    "边防": "边疆防御、驻军布防、边境管理",
                    "外交往来": "与藩属国、外国的使节往来"
                },
                "财政与经济事务": {
                    "财政内容": "财政收支数额、国库管理、赋税征收",
                    "商业贸易": "商品交易、市场管理、商税政策",
                    "经济政策": "影响经济的制度"
                },
                "科举与教育": {
                    "科举": "科举考试流程、录取规则"
                }
            },
            "1": {  # 问题类
                "不确定": {
                    "待补充": "暂时无法明确归类的问题内容"
                },
                "行政失职": {
                    "待补充": "官员行政失职的具体表现"
                },
                "腐败": {
                    "待补充": "官员贪腐行为"
                }
            }
        }

    def load_data_from_json(self, file_path, default_data=None):
        """通用 JSON 文件加载函数"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告：无法加载 {file_path}，使用默认数据。错误: {e}")
                return default_data if default_data is not None else {}
        return default_data if default_data is not None else {}

    def save_data_to_json(self, data, file_path):
        """通用 JSON 文件保存函数"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"错误：无法保存数据到 {file_path}. 错误: {e}")

    def load_all_data(self):
        """加载所有持久化数据"""
        self.classifiedData = self.load_data_from_json(CLASSIFIED_DATA_FILE)
        self.translationHistory = self.load_data_from_json(HISTORY_FILE, default_data=[])
        self.customKeywordMap = self.load_data_from_json(CUSTOM_KEYWORD_FILE)
        self._update_merged_keyword_map()

    def _update_merged_keyword_map(self):
        """合并《清实录》自带词库和自定义词库"""
        self.mergedKeywordMap = {**self.qingShiluKeywords, **self.customKeywordMap}

        # services-未拆分.py (DataModel 类的 save_classified_text 方法 - 确保 article_id 存在)
        # 请务必检查缩进！

        # services-未拆分.py (DataModel 类的 save_classified_text 方法 - 最终修正)

    def save_classified_text(self, original_text, translation, classification_key, article_id: str | None = None):
        """保存已分类的文本，新增 article_id 用于批量处理的标识（JS: saveClassification）"""

        # 示例 key: '0/赈灾与民生保障/赈灾'
        # 确保 time 模块已导入
        import time

        l1, l2, l3 = classification_key.split('/')

        if l1 not in self.classifiedData:
            self.classifiedData[l1] = {}
        if l2 not in self.classifiedData[l1]:
            self.classifiedData[l1][l2] = {}
        if l3 not in self.classifiedData[l1][l2]:
            self.classifiedData[l1][l2][l3] = []

        new_entry = {
            "originalText": original_text,
            "translation": translation,
            "articleId": article_id,  # 【新增】保存条文ID
            "timestamp": time.time()
        }
        self.classifiedData[l1][l2][l3].append(new_entry)

        # 【关键修正】直接使用顶部的 CLASSIFIED_DATA_FILE 变量
        self.save_data_to_json(self.classifiedData, CLASSIFIED_DATA_FILE)

    def update_custom_keywords(self, category_key, keywords):
        """更新自定义关键词并保存（JS: saveKeywords）"""
        # key 格式: "事务类-赈灾与民生保障-赈灾"
        if category_key not in self.customKeywordMap:
            self.customKeywordMap[category_key] = {"keywords": [], "description": "自定义关键词"}

        self.customKeywordMap[category_key]['keywords'] = keywords

        self._update_merged_keyword_map()
        self.save_data_to_json(self.customKeywordMap, CUSTOM_KEYWORD_FILE)

    def find_category_cases(self, l1, l2, l3):
        """查找指定分类下的案例文本"""
        return [
            item['originalText']
            for item in self.classifiedData.get(l1, {}).get(l2, {}).get(l3, [])
        ]

    # services-未拆分.py (DataModel 类的增强)

    def get_all_classified_data(self):
        """返回所有的分类数据（classifiedData）"""
        return self.classifiedData

    def export_classified_data_to_csv(self, file_path):
        """将所有分类数据导出为 CSV 格式"""
        import csv

        data = self.classifiedData
        # CSV 头部
        header = ["Level1", "Level2", "Level3", "OriginalText", "Translation", "ArticleId", "Timestamp"]

        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)

                # 遍历三级结构
                for l1_key, l1_data in data.items():
                    for l2_key, l2_data in l1_data.items():
                        for l3_key, articles in l2_data.items():
                            for article in articles:
                                writer.writerow([
                                    l1_key,
                                    l2_key,
                                    l3_key,
                                    article['originalText'].replace('\n', ' ').strip(),  # 移除换行符
                                    article.get('translation', 'N/A').replace('\n', ' ').strip(),
                                    article.get('articleId', 'N/A'),
                                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(article['timestamp']))
                                ])
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False

class QingShiluService:
    """
    负责执行核心分析算法和管理数据操作。
    取代了 JS 类中的所有业务逻辑方法。
    """

    def __init__(self):
        self.model = DataModel()

    # --- 核心分析方法 (JS: translateAndRecommend) ---

    def run_full_analysis(self, original_text: str):
        """
        执行完整的智能分析流程（耗时操作，需由 WorkerThread 调用）。
        """
        # 模拟 BERT/NLP 模型的推理时间 (JS 模拟的异步耗时)
        time.sleep(1.5)

        core_info = self._extract_core_info(original_text)
        translation = self._simulate_optimized_translation(original_text, core_info)
        keywords = self._extract_keywords(original_text)
        recommendations = self._get_classification_recommendations(original_text, keywords)
        similar_texts = self._find_similar_texts(original_text)

        return {
            'translation': translation,
            'core_info': core_info,
            'keywords': keywords,
            'recommendations': recommendations,
            'similar_texts': similar_texts,
            'category_structure': self.model.categoryStructure  # 将结构也返回给 Controller
        }

    # --- 内部辅助方法 (JS 核心逻辑的 Python 翻译) ---

    def _extract_core_info(self, text):
        """提取核心信息（JS: extractCoreInfo）"""
        import re

        # 提取主体
        subject = ""
        # 匹配 JS 复杂的正则表达式
        subject_matches = re.search(r"(○\d+)?\s*(\w+?巡抚|\w+?总督|\w+?按察使|\w+?知府|\w+?知县|皇上|皇帝|朝廷|部议)",
                                    text)
        if subject_matches:
            # Python re.search 返回 groups
            subject = subject_matches.group(2) if subject_matches.group(2) else subject_matches.group(1)

        # 提取核心动作
        action = ""
        action_keywords = ["参奏", "题参", "疏报", "谕令", "谕", "抚恤", "赈济", "剿", "捕", "审", "判", "任免", "调",
                           "革职"]
        for keyword in action_keywords:
            if keyword in text:
                action = keyword
                break

        # 提取事件性质 (基于关键字的简单判断)
        nature = ""
        if "不效力" in text or "徇私" in text or "贪暴" in text or "失职" in text:
            nature = "官员失职问题"
        elif "被灾" in text or "抚恤" in text or "赈济" in text:
            nature = "灾害救济事务"
        # ... (省略其他性质判断)

        return {"subject": subject, "action": action, "nature": nature}

    def _simulate_optimized_translation(self, original_text, core_info):
        """优化的翻译（JS: simulateOptimizedTranslation）"""

        translation = f"【核心信息】主体: {core_info.get('subject', '无')}, 性质: {core_info.get('nature', '无')}\n\n"
        translation += "这是 Service 层对原文的白话文翻译。\n\n"

        # 添加术语注释
        terms = {
            "题参": "上奏参劾",
            "蠲免": "免除赋税",
            "赈粜": "平价卖粮救灾",
            "平粜": "平价卖粮",
        }

        for term, note in terms.items():
            if term in original_text:
                translation += f"【术语注释】'{term}' 意为 '{note}'。\n"

        return translation

    def _extract_keywords(self, text):
        """提取关键词（JS: extractKeywords）"""
        all_keywords = set()

        # 从合并的词库中提取关键词
        for category, data in self.model.mergedKeywordMap.items():
            keywords = data['keywords']
            for keyword in keywords:
                if keyword in text:
                    all_keywords.add(keyword)

        return list(all_keywords)

    def _get_classification_recommendations(self, text, keywords):
        """获取分类推荐（JS: getClassificationRecommendations）"""
        recommendations = []
        category_scores = {}

        # 计算每个分类的匹配分数
        for category, data in self.model.mergedKeywordMap.items():
            category_keywords = data['keywords']
            score = 0

            for keyword in keywords:
                if keyword in category_keywords:
                    score += 1

            if score > 0:
                category_scores[category] = score

        # 排序并返回前3个推荐
        sorted_categories = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)[:3]

        for category, score in sorted_categories:
            parts = category.split('-')
            level1 = parts[0]
            level2 = parts[1]
            level3 = parts[2]

            recommendations.append({
                "category": category,
                "level1": level1,
                "level2": level2,
                "level3": level3,
                "score": score,
                "reason": self.model.mergedKeywordMap[category].get('description', '无'),
                "matchedKeywords": [kw for kw in keywords if kw in self.model.mergedKeywordMap[category]['keywords']]
            })

        return recommendations

    def _find_similar_texts(self, text):
        """查找相似文本（JS: findSimilarTexts）"""
        all_texts = []

        # 收集所有已分类的文本
        for l1, v1 in self.model.classifiedData.items():
            for l2, v2 in v1.items():
                for l3, texts in v2.items():
                    for t in texts:
                        all_texts.append({
                            **t,
                            "categoryPath": f"{l1}集 → {l2} → {l3}"
                        })

        similar_texts = []
        text_keywords = self._extract_keywords(text)

        for stored_text in all_texts:
            stored_keywords = self._extract_keywords(stored_text['originalText'])
            common_keywords = [kw for kw in text_keywords if kw in stored_keywords]

            if len(common_keywords) >= 2:
                similar_texts.append({
                    **stored_text,
                    "similarity": len(common_keywords),
                    "commonKeywords": common_keywords
                })

        # 按相似度排序，返回前3个
        return sorted(similar_texts, key=lambda x: x['similarity'], reverse=True)[:3]

    # --- 数据管理方法 ---

        # services-未拆分.py (QingShiluService 类的 save_classification_result 方法 - 确保 article_id 存在)

    def save_classification_result(self, original_text, translation, classification_key,
                                   article_id: str | None = None):
        """保存单条分类结果，新增 article_id 参数"""
        # key 格式: '0/赈灾与民生保障/赈灾'
        # 注意：这里将 article_id 传递给了 DataModel
        self.model.save_classified_text(original_text, translation, classification_key, article_id)

    # --- 关键词和分类管理方法 ---

    def get_all_categories_map(self):
        """获取所有分类键值和描述的扁平化映射"""
        return self.model.mergedKeywordMap

    def get_keywords_for_category(self, category_key):
        """获取指定分类的关键词列表"""
        return self.model.mergedKeywordMap.get(category_key, {}).get('keywords', [])

    def save_keywords(self, category_key, keywords):
        """保存关键词并更新模型"""
        self.model.update_custom_keywords(category_key, keywords)

    def get_category_structure(self):
        """获取三级分类结构"""
        return self.model.categoryStructure


# services-未拆分.py (FileManager 类的增强)

# services-未拆分.py (FileManager 类的修复和完整代码)
import os
import re
from PySide6.QtWidgets import QFileDialog, QWidget  # 确保这些已导入


class FileManager:
    """
    负责文件操作相关的核心业务逻辑，现包含多条历史条文的批量处理。
    """

    def __init__(self, qingshilu_service):
        self.qingshilu_service = qingshilu_service
        self.selected_files = []
        # 存储批量分析结果，包含条文的列表
        # 结构: [{"article_id": str, "originalText": str, "analysis": dict, "classification_key": str | None}, ...]
        self.batch_articles = []

    # === 修复缺失的方法 ===
    def select_batch_files(self, parent_widget: QWidget) -> list[str] | None:
        """打开文件对话框，选择文件列表，并更新内部状态"""
        # 注意：QFileDialog 需要在 services-未拆分.py 顶部导入
        files, _ = QFileDialog.getOpenFileNames(
            parent_widget, "选择批量文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if files:
            self.selected_files = files
            return files

        self.selected_files = []
        return None

    def get_selected_files(self) -> list[str]:
        """返回当前选中的文件列表"""
        return self.selected_files

    # ========================

    def _split_text_into_articles(self, text: str, file_name: str) -> list[dict]:
        """
        根据“○”或“○+序号”的特征，将文本拆分成多条历史条文。

        注意：原始代码中 re.split 的逻辑复杂且不完整，现只保留可靠的 re.finditer 逻辑。
        """

        # 在文本开头强制添加一个标记，以便捕获第一个条文
        # 避免第一个条文前没有换行符导致无法匹配
        temp_text = "\n○1 " + text.strip()

        # 使用 finditer 找到所有匹配的条文块
        # (○\d*\s*) 是条文编号
        # (.*?) 是条文内容（非贪婪匹配）
        # (?=\n[ \t]*○\d*\s*|\Z) 是正向前瞻，确保内容在下一个条文标记或文件末尾(\Z)处停止
        articles_re_match = re.finditer(r"(\n[ \t]*)(○\d*\s*)(.*?)(?=\n[ \t]*○\d*\s*|\Z)", temp_text, re.DOTALL)

        final_articles = []
        article_index = 1

        # 移除 re.split 相关的冗余和不完整代码，直接使用可靠的 finditer 结果
        for match in articles_re_match:
            # group(2) 是 ○编号, group(3) 是条文内容
            article_content = (match.group(2) + match.group(3)).strip()

            # 为每条条文生成一个唯一ID：文件名_序号
            article_id = f"{os.path.basename(file_name).split('.')[0]}_{article_index}"

            final_articles.append({
                "article_id": article_id,
                "originalText": article_content
            })
            article_index += 1

        return final_articles

    def process_files(self):
        """
        执行批量分析的核心调度逻辑：读取文件 -> 拆分条文 -> 分析条文。
        """
        files_to_process = self.get_selected_files()
        if not files_to_process:
            return "错误：没有文件可供处理。"

        self.batch_articles = []
        total_files = len(files_to_process)
        article_count = 0

        for i, file_path in enumerate(files_to_process):
            try:
                # 1. 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()

                # 2. 拆分文件为多条历史条文
                articles = self._split_text_into_articles(text, file_path)
                article_count += len(articles)

                # 3. 对每条条文进行分析
                for article in articles:
                    # 调用核心分析服务进行分析
                    analysis_result = self.qingshilu_service.run_full_analysis(article['originalText'])

                    self.batch_articles.append({
                        "article_id": article['article_id'],
                        "originalText": article['originalText'],
                        "analysis": analysis_result,
                        "classification_key": None  # 初始时未分类
                    })

                print(
                    f"Service: 批量处理文件 {os.path.basename(file_path)} 完成，拆分出 {len(articles)} 条条文 ({i + 1}/{total_files})")

            except Exception as e:
                error_msg = f"处理文件 {os.path.basename(file_path)} 失败: {e}"
                print(error_msg)
                # 记录文件级别的错误 (将错误作为单独的条目记录)
                self.batch_articles.append({"article_id": f"ERROR_{os.path.basename(file_path)}", "error": error_msg})

        return f"批量处理成功：共处理 {total_files} 个文件，拆分并分析 {article_count} 条条文。"

    def get_batch_articles(self):
        """返回本次批量处理的条文结果"""
        return self.batch_articles

    def update_article_classification(self, article_id: str, classification_key: str):
        """更新批量条文中的单个条文分类"""
        for article in self.batch_articles:
            if article.get('article_id') == article_id:
                article['classification_key'] = classification_key
                break