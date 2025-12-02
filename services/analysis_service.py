# services/analysis_service.py
# ----------------------------------------------------
# QingShiluService 类：核心分析算法、业务逻辑

import re

# 从同级模块导入 DataModel
from gemini.services.data_model import DataModel


class QingShiluService:
    """
    负责执行核心分析算法和管理数据操作。
    """

    def __init__(self):
        self.model = DataModel()

    # --- 核心分析方法 (JS: translateAndRecommend) ---

    def run_full_analysis(self, original_text: str):
        """
        执行完整的智能分析流程（耗时操作，需由 WorkerThread 调用）。
        """
        # 模拟 BERT/NLP 模型的推理时间 (JS 模拟的异步耗时)
        # 🌟 移除或注释掉 time.sleep(1.5)
        # time.sleep(1.5)

        core_info = self._extract_core_info(original_text)

        # 🌟 调用现在位于此类的内部
        keywords = self._extract_keywords(original_text)

        translation = self._simulate_optimized_translation(original_text, core_info)

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
        # ... (您原有的 _extract_core_info 完整内容) ...
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
        # ... (您原有的 _simulate_optimized_translation 完整内容) ...
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

    # 🌟 【关键修复】正确的位置，在主 QingShiluService 类内部
    def _extract_keywords(self, text):
        """提取关键词（JS: extractKeywords）"""
        all_keywords = set()

        # 确保所有空格、换行符被清理 (生产代码版本)
        clean_text = text.replace('\n', '').replace('\r', '').strip()

        # 从合并的词库中提取关键词
        for category, data in self.model.mergedKeywordMap.items():
            keywords = data['keywords']
            for keyword in keywords:
                # 匹配逻辑保持不变
                if keyword in clean_text:
                    all_keywords.add(keyword)

        return list(all_keywords)

    def _get_classification_recommendations(self, text, keywords):
        """获取分类推荐（JS: getClassificationRecommendations）"""
        # ... (您原有的 _get_classification_recommendations 完整内容) ...
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
        # ... (您原有的 _find_similar_texts 完整内容) ...
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
        text_keywords = self._extract_keywords(text)  # 注意：这里会递归调用 _extract_keywords

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

    # --- 数据管理方法 (调用 DataModel) ---

    def save_classification_result(self, original_text, translation, classification_key,
                                   article_id: str | None = None):
        """保存单条分类结果，新增 article_id 参数"""
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