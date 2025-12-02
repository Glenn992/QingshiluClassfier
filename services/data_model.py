# services/data_model.py

import os
import json
import time
import csv
import traceback

# 🌟【注意】我们保持 category_structure.py 文件不变，它导入的是原始结构
from gemini.services.category_structure import DEFAULT_CATEGORY_STRUCTURE
from gemini.services.keywords_data import QING_SHILU_KEYWORDS
from gemini.services.constants import CLASSIFIED_DATA_FILE, CUSTOM_KEYWORD_FILE, HISTORY_FILE

# L1 键的显示名称映射，用于在不修改 category_structure.py 的前提下生成 'name' 字段
# 这是根据您提供的 category_structure.py 中的注释确定的。
L1_NAME_MAP = {
    "0": "事务类 (Affairs)",
    "1": "问题类 (Issues)",
}


class DataModel:
    """
    负责管理和持久化应用的所有数据：分类结构、关键词、历史记录。
    """

    def __init__(self):
        self.classifiedData = {}
        self.translationHistory = []
        self.customKeywordMap = {}
        # categoryStructure 存储的是 category_structure.py 导入的原始结构
        self.categoryStructure = self._get_default_category_structure()
        self.qingShiluKeywords = self._get_qing_shilu_keywords()

        self.mergedKeywordMap = {**self.qingShiluKeywords}

        self.load_all_data()

        print(f"DEBUG(Model): Merged Keyword Map size: {len(self.mergedKeywordMap)}")

    def _get_qing_shilu_keywords(self):
        """加载《清实录》专属词库"""
        return QING_SHILU_KEYWORDS

    def _get_default_category_structure(self):
        """加载默认分类结构"""
        return DEFAULT_CATEGORY_STRUCTURE

    def get_category_structure(self):
        """
        提供给外部获取完整的分类结构。
        🌟【核心修复】: 动态地为 L1 键添加 'name' 字段和 'levels' 嵌套，以适应 UI 需求。
        """
        safe_structure = {}
        for l1_key, l1_data in self.categoryStructure.items():

            l1_name = L1_NAME_MAP.get(l1_key, f"未知 L1 ({l1_key})")

            # 检查 L1_data 是否是字典 (包含 L2 键)
            if isinstance(l1_data, dict) and l1_data:

                # 构造符合 UI (stats_tab.py) 期望的结构:
                # { "0": { "name": "事务类", "levels": { "赈灾与民生保障": {...} } } }
                safe_structure[l1_key] = {
                    'name': l1_name,
                    # 将原始 L1 键下的所有内容视为 L2/L3 的 'levels'
                    'levels': l1_data
                }
            else:
                print(f"警告: L1 分类结构中键 '{l1_key}' 的数据格式错误，已忽略。")

        # 🌟【调试信息】添加日志，确认返回给 UI 的结构是否包含 'name'
        if safe_structure:
            sample_key = next(iter(safe_structure))
            print(
                f"DEBUG(Model): get_category_structure output sample (L1 key '{sample_key}'): {list(safe_structure[sample_key].keys())}")

        return safe_structure

    # =================================================================
    # 以下方法保持不变或仅有轻微调整以确保兼容性
    # =================================================================

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

    def save_classified_text(self, original_text, translation, classification_key, article_id: str | None = None):
        """保存已分类的文本，新增 article_id 用于批量处理的标识（JS: saveClassification）"""

        # 示例 key: '0/赈灾与民生保障/赈灾'
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
            "articleId": article_id,
            "timestamp": time.time()
        }

        # 检查是否已存在具有相同 articleId 的条目
        is_updated = False
        if article_id:
            try:
                articles_list = self.classifiedData[l1][l2][l3]
                for i, existing_entry in enumerate(articles_list):
                    if existing_entry.get("articleId") == article_id:
                        articles_list[i] = new_entry
                        is_updated = True
                        break
            except KeyError:
                pass

        if not is_updated:
            self.classifiedData[l1][l2][l3].append(new_entry)

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

    def get_all_classified_data(self):
        """返回所有的分类数据（classifiedData）"""
        return self.classifiedData

    # =================================================================
    # 🌟【新增功能】统计和筛选数据方法 (保持兼容性)
    # =================================================================

    def get_classified_stats(self, filter_key: str | None = None):
        """
        根据 filter_key 返回结构化的分类统计数据。
        注意：此方法是基于 self.categoryStructure 的 L2/L3 键名来遍历 classifiedData 的。
        """

        # 解析筛选键
        if filter_key:
            parts = filter_key.split('/')
            l1_filter = parts[0] if len(parts) > 0 else None
            l2_filter = parts[1] if len(parts) > 1 else None
            l3_filter = parts[2] if len(parts) > 2 else None
        else:
            l1_filter, l2_filter, l3_filter = None, None, None

        stats_result = {}
        total_count_all = 0

        # 遍历 classifiedData 的 L1 键 ('0', '1')
        for l1_key, l1_data in self.classifiedData.items():
            if l1_filter and l1_key != l1_filter:
                continue

            # 🌟 使用 get_category_structure 获得的结构来获取 L1 name 和 L2 levels
            l1_cat_structure = self.get_category_structure().get(l1_key)
            if not l1_cat_structure:
                print(f"警告: classifiedData 中发现未知的 L1 键 '{l1_key}'。跳过统计。")
                continue

            l1_name = l1_cat_structure.get('name', f"未知 L1 ({l1_key})")
            l1_levels = l1_cat_structure.get('levels', {})  # 获取 L2/L3 嵌套结构

            l1_stats = {
                'name': l1_name,
                'count': 0,
                'levels': {}
            }

            # 遍历 L2 键 (这里使用 categoryStructure 中的 L2 键名，确保完整性)
            for l2_name, l3_map in l1_levels.items():
                if l2_filter and l2_name != l2_filter:
                    continue

                # 从实际分类数据中获取 L2 数据 (即 classifiedData[l1_key][l2_name])
                l2_data_actual = l1_data.get(l2_name, {})

                l2_stats = {
                    'count': 0,
                    'levels': {}
                }

                # 遍历 L3 键
                for l3_name in l3_map.keys():
                    if l3_filter and l3_name != l3_filter:
                        continue

                    # 从实际数据中获取 L3 文章列表
                    articles = l2_data_actual.get(l3_name, [])
                    l3_count = len(articles)

                    # 累加统计
                    l2_stats['count'] += l3_count
                    if l3_filter is None:
                        l2_stats['levels'][l3_name] = l3_count

                # 如果 L2 有数据 (或者 L2 没被筛选但 L3 有数据)
                if l2_stats['count'] > 0:
                    l1_stats['count'] += l2_stats['count']
                    if l2_filter is None:
                        l1_stats['levels'][l2_name] = l2_stats

            # 如果 L1 有数据
            if l1_stats['count'] > 0:
                stats_result[l1_key] = l1_stats
                total_count_all += l1_stats['count']

        # 调整结果结构以适应 StatsTabWidget 的渲染 (省略了过滤细节，保持代码完整性)
        if l3_filter:
            final_result = {}
            if l1_filter in stats_result:
                l1_stats = stats_result[l1_filter]

                l2_stats_temp = l1_stats['levels'].get(l2_filter, {'count': 0, 'levels': {}})
                actual_l3_count = len(self.classifiedData.get(l1_filter, {}).get(l2_filter, {}).get(l3_filter, []))

                l2_stats_temp['count'] = actual_l3_count
                l2_stats_temp['levels'] = {l3_filter: actual_l3_count}

                l1_stats['levels'] = {l2_filter: l2_stats_temp}
                l1_stats['count'] = actual_l3_count
                final_result[l1_filter] = l1_stats
            return final_result

        return stats_result

    def _get_filtered_articles(self, filter_key: str | None = None):
        """根据 filter_key 获取所有匹配的条目列表 (用于导出)"""

        articles_to_export = []

        # 解析筛选键
        if filter_key:
            parts = filter_key.split('/')
            l1_filter = parts[0] if len(parts) > 0 else None
            l2_filter = parts[1] if len(parts) > 1 else None
            l3_filter = parts[2] if len(parts) > 2 else None
        else:
            l1_filter, l2_filter, l3_filter = None, None, None

        for l1_key, l1_data in self.classifiedData.items():
            if l1_filter and l1_key != l1_filter:
                continue

            for l2_name, l2_data in l1_data.items():
                if l2_filter and l2_name != l2_filter:
                    continue

                for l3_name, articles in l2_data.items():
                    if l3_filter and l3_name != l3_filter:
                        continue

                    for article in articles:
                        # 构造完整行数据
                        articles_to_export.append({
                            "Level1": l1_key,
                            "Level2": l2_name,
                            "Level3": l3_name,
                            "OriginalText": article['originalText'],
                            "Translation": article.get('translation', 'N/A'),
                            "ArticleId": article.get('articleId', 'N/A'),
                            "Timestamp": article['timestamp']
                        })

        return articles_to_export

    def export_classified_data_to_csv(self, file_path, filter_key: str | None = None):
        """将所有分类数据导出为 CSV 格式，可根据 filter_key 筛选"""

        articles_to_export = self._get_filtered_articles(filter_key)

        if not articles_to_export:
            print("警告：没有数据可以导出。")
            try:
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Level1", "Level2", "Level3", "OriginalText", "Translation", "ArticleId", "Timestamp"])
                return True
            except Exception as e:
                print(f"Error creating empty CSV file: {e}")
                return False

        header = ["Level1", "Level2", "Level3", "OriginalText", "Translation", "ArticleId", "Timestamp"]

        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)

                for article in articles_to_export:
                    # 格式化时间戳
                    formatted_time = time.strftime(
                        '%Y-%m-%d %H:%M:%S',
                        time.localtime(article['Timestamp'])
                    )

                    writer.writerow([
                        article['Level1'],
                        article['Level2'],
                        article['Level3'],
                        article['OriginalText'].replace('\n', ' ').strip(),
                        article['Translation'].replace('\n', ' ').strip(),
                        article['ArticleId'],
                        formatted_time
                    ])
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            print(traceback.format_exc())
            return False
