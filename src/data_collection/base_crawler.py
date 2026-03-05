"""
数据采集基类
提供统一的数据采集接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pathlib import Path
import json
import time
from datetime import datetime
from loguru import logger
import pandas as pd


class BaseCrawler(ABC):
    """数据爬虫基类"""
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        log_file = Path("logs") / f"{self.__class__.__name__}_{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(exist_ok=True)
        logger.add(log_file, rotation="500 MB", retention="30 days")
    
    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict]:
        """
        获取原始数据
        
        Returns:
            List[Dict]: 原始数据列表
        """
        pass
    
    @abstractmethod
    def parse(self, raw_data: List[Dict]) -> List[Dict]:
        """
        解析原始数据
        
        Args:
            raw_data: 原始数据
            
        Returns:
            List[Dict]: 解析后的标准化数据
        """
        pass
    
    def validate(self, data: Dict) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 单条数据
            
        Returns:
            bool: 是否有效
        """
        required_fields = self.get_required_fields()
        return all(field in data and data[field] for field in required_fields)
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        返回必需字段列表
        
        Returns:
            List[str]: 必需字段名称
        """
        pass
    
    def save(self, data: List[Dict], filename: Optional[str] = None):
        """
        保存数据到JSONL文件
        
        Args:
            data: 数据列表
            filename: 文件名 (可选)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.__class__.__name__.lower()}_{timestamp}.jsonl"
        
        output_path = self.output_dir / filename
        
        # 验证并保存
        valid_data = [item for item in data if self.validate(item)]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in valid_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        logger.info(f"✅ 保存 {len(valid_data)}/{len(data)} 条数据到 {output_path}")
        
        return output_path
    
    def run(self, save_to_file: bool = True, **kwargs) -> List[Dict]:
        """
        执行完整的爬取流程
        
        Args:
            save_to_file: 是否保存到文件
            **kwargs: 传递给fetch的参数
            
        Returns:
            List[Dict]: 处理后的数据
        """
        logger.info(f"🚀 开始执行 {self.__class__.__name__}")
        start_time = time.time()
        
        try:
            # 1. 获取数据
            logger.info("📥 正在获取数据...")
            raw_data = self.fetch(**kwargs)
            logger.info(f"✅ 获取到 {len(raw_data)} 条原始数据")
            
            # 2. 解析数据
            logger.info("🔄 正在解析数据...")
            parsed_data = self.parse(raw_data)
            logger.info(f"✅ 解析完成 {len(parsed_data)} 条数据")
            
            # 3. 保存数据
            if save_to_file:
                self.save(parsed_data)
            
            elapsed = time.time() - start_time
            logger.info(f"✅ 执行完成,耗时 {elapsed:.2f}秒")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"❌ 执行失败: {str(e)}")
            raise
    
    def to_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """
        转换为DataFrame
        
        Args:
            data: 数据列表
            
        Returns:
            pd.DataFrame: 数据框
        """
        return pd.DataFrame(data)


class BaseProcessor(ABC):
    """数据处理基类"""
    
    def __init__(self):
        pass
    
    @abstractmethod
    def process(self, data: List[Dict]) -> List[Dict]:
        """
        处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            List[Dict]: 处理后的数据
        """
        pass
    
    def batch_process(self, data: List[Dict], batch_size: int = 100) -> List[Dict]:
        """
        批量处理数据
        
        Args:
            data: 输入数据
            batch_size: 批次大小
            
        Returns:
            List[Dict]: 处理后的数据
        """
        results = []
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            batch_results = self.process(batch)
            results.extend(batch_results)
            logger.info(f"处理进度: {min(i+batch_size, len(data))}/{len(data)}")
        
        return results


class DataCleaner(BaseProcessor):
    """数据清洗器"""
    
    def process(self, data: List[Dict]) -> List[Dict]:
        """
        清洗数据
        - 去重
        - 去除无效字段
        - 标准化格式
        """
        cleaned = []
        seen_ids = set()
        
        for item in data:
            # 去重
            item_id = self._get_item_id(item)
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            
            # 清洗
            cleaned_item = self._clean_item(item)
            if cleaned_item:
                cleaned.append(cleaned_item)
        
        logger.info(f"清洗后剩余 {len(cleaned)}/{len(data)} 条数据")
        return cleaned
    
    def _get_item_id(self, item: Dict) -> str:
        """生成唯一ID"""
        # 可根据具体数据结构自定义
        return f"{item.get('title', '')}_{item.get('publish_time', '')}"
    
    def _clean_item(self, item: Dict) -> Optional[Dict]:
        """清洗单条数据"""
        # 去除空白字符
        cleaned = {}
        for k, v in item.items():
            if isinstance(v, str):
                v = v.strip()
                if not v:
                    continue
            cleaned[k] = v
        
        return cleaned if cleaned else None
