"""
区块链技能 - 为区块链智能体提供溯源和数据上链功能
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class TransactionType(Enum):
    """交易类型枚举"""
    PLANTING = "种植"
    FERTILIZATION = "施肥"
    PEST_CONTROL = "病虫害防治"
    HARVEST = "收获"
    PROCESSING = "加工"
    TRANSPORT = "运输"
    STORAGE = "存储"
    SALE = "销售"

@dataclass
class BlockchainRecord:
    """区块链记录"""
    record_id: str
    transaction_type: TransactionType
    farm_id: str
    crop_id: str
    timestamp: str
    data: Dict[str, Any]
    previous_hash: str
    current_hash: str
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['transaction_type'] = self.transaction_type.value
        return data

class BlockchainSkill:
    """区块链技能"""
    
    def __init__(self, node_url: Optional[str] = None):
        """
        初始化区块链技能
        
        Args:
            node_url: 区块链节点URL（如Hyperledger Fabric）
        """
        self.node_url = node_url or "http://localhost:7050"
        self.chain = []  # 本地链（简化版）
        self.pending_transactions = []
        
        # 创建创世区块
        self._create_genesis_block()
    
    def _create_genesis_block(self):
        """创建创世区块"""
        genesis_data = {
            "message": "AI农业决策系统区块链初始化",
            "timestamp": datetime.now().isoformat(),
            "creator": "system"
        }
        
        genesis_record = BlockchainRecord(
            record_id="genesis_0001",
            transaction_type=TransactionType.PLANTING,
            farm_id="system",
            crop_id="system",
            timestamp=datetime.now().isoformat(),
            data=genesis_data,
            previous_hash="0" * 64,
            current_hash=self._calculate_hash(genesis_data, "0" * 64)
        )
        
        self.chain.append(genesis_record)
        logger.info("创世区块创建完成")
    
    def record_planting(self, farm_id: str, crop_id: str, 
                       planting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录种植信息到区块链
        
        Args:
            farm_id: 农场ID
            crop_id: 作物ID
            planting_data: 种植数据
        
        Returns:
            区块链记录
        """
        record_data = {
            **planting_data,
            "action": "planting",
            "farm_id": farm_id,
            "crop_id": crop_id
        }
        
        return self._add_to_blockchain(
            transaction_type=TransactionType.PLANTING,
            farm_id=farm_id,
            crop_id=crop_id,
            data=record_data
        )
    
    def record_fertilization(self, farm_id: str, crop_id: str,
                           fertilizer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录施肥信息到区块链
        
        Args:
            farm_id: 农场ID
            crop_id: 作物ID
            fertilizer_data: 施肥数据
        
        Returns:
            区块链记录
        """
        record_data = {
            **fertilizer_data,
            "action": "fertilization",
            "farm_id": farm_id,
            "crop_id": crop_id
        }
        
        return self._add_to_blockchain(
            transaction_type=TransactionType.FERTILIZATION,
            farm_id=farm_id,
            crop_id=crop_id,
            data=record_data
        )
    
    def record_pest_control(self, farm_id: str, crop_id: str,
                          control_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录病虫害防治信息到区块链
        
        Args:
            farm_id: 农场ID
            crop_id: 作物ID
            control_data: 防治数据
        
        Returns:
            区块链记录
        """
        record_data = {
            **control_data,
            "action": "pest_control",
            "farm_id": farm_id,
            "crop_id": crop_id
        }
        
        return self._add_to_blockchain(
            transaction_type=TransactionType.PEST_CONTROL,
            farm_id=farm_id,
            crop_id=crop_id,
            data=record_data
        )
    
    def record_harvest(self, farm_id: str, crop_id: str,
                      harvest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        记录收获信息到区块链
        
        Args:
            farm_id: 农场ID
            crop_id: 作物ID
            harvest_data: 收获数据
        
        Returns:
            区块链记录
        """
        record_data = {
            **harvest_data,
            "action": "harvest",
            "farm_id": farm_id,
            "crop_id": crop_id
        }
        
        return self._add_to_blockchain(
            transaction_type=TransactionType.HARVEST,
            farm_id=farm_id,
            crop_id=crop_id,
            data=record_data
        )
    
    def trace_product(self, product_id: str) -> Dict[str, Any]:
        """
        追溯产品全生命周期
        
        Args:
            product_id: 产品ID
        
        Returns:
            追溯结果
        """
        # 在实际区块链中，这里应该查询链上数据
        # 这里返回模拟数据
        
        trace_records = []
        for record in self.chain:
            if (record.crop_id == product_id or 
                record.data.get("product_id") == product_id):
                trace_records.append(record.to_dict())
        
        if not trace_records:
            return {
                "product_id": product_id,
                "found": False,
                "message": "未找到该产品的追溯记录"
            }
        
        # 按时间排序
        trace_records.sort(key=lambda x: x['timestamp'])
        
        # 构建追溯链
        trace_chain = []
        for i, record in enumerate(trace_records):
            trace_chain.append({
                "step": i + 1,
                "transaction_type": record['transaction_type'],
                "timestamp": record['timestamp'],
                "data": record['data'],
                "block_hash": record['current_hash']
            })
        
        return {
            "product_id": product_id,
            "found": True,
            "total_records": len(trace_chain),
            "trace_chain": trace_chain,
            "summary": self._generate_trace_summary(trace_chain)
        }
    
    def verify_product(self, product_id: str) -> Dict[str, Any]:
        """
        验证产品真实性
        
        Args:
            product_id: 产品ID
        
        Returns:
            验证结果
        """
        trace_result = self.trace_product(product_id)
        
        if not trace_result['found']:
            return {
                "product_id": product_id,
                "verified": False,
                "reason": "无追溯记录"
            }
        
        # 检查区块链完整性
        chain_valid = self._validate_chain()
        
        # 检查产品数据完整性
        data_valid = self._validate_product_data(trace_result['trace_chain'])
        
        verified = chain_valid and data_valid
        
        return {
            "product_id": product_id,
            "verified": verified,
            "chain_valid": chain_valid,
            "data_valid": data_valid,
            "verification_score": 0.95 if verified else 0.3,
            "certificate": self._generate_certificate(product_id, verified)
        }
    
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """
        获取区块链统计信息
        
        Returns:
            统计信息
        """
        total_blocks = len(self.chain)
        total_transactions = sum(1 for block in self.chain if block.record_id != "genesis_0001")
        
        # 按交易类型统计
        type_stats = {}
        for block in self.chain:
            if block.record_id != "genesis_0001":
                t_type = block.transaction_type.value
                type_stats[t_type] = type_stats.get(t_type, 0) + 1
        
        return {
            "total_blocks": total_blocks,
            "total_transactions": total_transactions,
            "transactions_by_type": type_stats,
            "chain_height": total_blocks,
            "last_block_hash": self.chain[-1].current_hash if self.chain else None,
            "blockchain_size_kb": total_blocks * 1.5,  # 估算
            "integrity_check": self._validate_chain()
        }
    
    def _add_to_blockchain(self, transaction_type: TransactionType,
                          farm_id: str, crop_id: str, 
                          data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加记录到区块链
        
        Args:
            transaction_type: 交易类型
            farm_id: 农场ID
            crop_id: 作物ID
            data: 交易数据
        
        Returns:
            区块链记录
        """
        # 获取前一个区块的哈希
        previous_hash = self.chain[-1].current_hash if self.chain else "0" * 64
        
        # 生成记录ID
        record_id = self._generate_record_id(transaction_type, farm_id, crop_id)
        
        # 计算当前哈希
        hash_data = {
            "record_id": record_id,
            "transaction_type": transaction_type.value,
            "farm_id": farm_id,
            "crop_id": crop_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "previous_hash": previous_hash
        }
        
        current_hash = self._calculate_hash(hash_data, previous_hash)
        
        # 创建区块链记录
        record = BlockchainRecord(
            record_id=record_id,
            transaction_type=transaction_type,
            farm_id=farm_id,
            crop_id=crop_id,
            timestamp=datetime.now().isoformat(),
            data=data,
            previous_hash=previous_hash,
            current_hash=current_hash
        )
        
        # 添加到链（简化版，实际应该通过共识机制）
        self.chain.append(record)
        
        logger.info(f"区块链记录添加成功: {record_id}")
        
        return {
            "success": True,
            "record_id": record_id,
            "block_hash": current_hash,
            "timestamp": record.timestamp,
            "transaction_type": transaction_type.value
        }
    
    def _calculate_hash(self, data: Dict, previous_hash: str) -> str:
        """计算哈希值"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        hash_input = f"{data_str}{previous_hash}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def _generate_record_id(self, transaction_type: TransactionType,
                           farm_id: str, crop_id: str) -> str:
        """生成记录ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        type_code = transaction_type.name[:3].lower()
        return f"{type_code}_{farm_id}_{crop_id}_{timestamp}"
    
    def _validate_chain(self) -> bool:
        """验证区块链完整性"""
        if len(self.chain) <= 1:
            return True
        
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # 检查前一个哈希是否匹配
            if current_block.previous_hash != previous_block.current_hash:
                logger.error(f"区块链完整性检查失败: 区块 {i}")
                return False
            
            # 重新计算当前哈希进行验证
            hash_data = {
                "record_id": current_block.record_id,
                "transaction_type": current_block.transaction_type.value,
                "farm_id": current_block.farm_id,
                "crop_id": current_block.crop_id,
                "timestamp": current_block.timestamp,
                "data": current_block.data,
                "previous_hash": current_block.previous_hash
            }
            
            calculated_hash = self._calculate_hash(hash_data, current_block.previous_hash)
            if calculated_hash != current_block.current_hash:
                logger.error(f"区块链哈希验证失败: 区块 {i}")
                return False
        
        return True
    
    def _validate_product_data(self, trace_chain: List[Dict]) -> bool:
        """验证产品数据完整性"""
        if not trace_chain:
            return False
        
        # 检查关键步骤是否存在
        required_steps = ["种植", "收获"]
        found_steps = [step['transaction_type'] for step in trace_chain]
        
        for step in required_steps:
            if step not in found_steps:
                logger.warning(f"产品数据不完整: 缺少 {step} 步骤")
                return False
        
        # 检查时间顺序
        timestamps = [step['timestamp'] for step in trace_chain]
        if timestamps != sorted(timestamps):
            logger.warning("产品时间顺序异常")
            return False
        
        return True
    
    def _generate_trace_summary(self, trace_chain: List[Dict]) -> Dict[str, Any]:
        """生成追溯摘要"""
        if not trace_chain:
            return {}
        
        # 提取关键信息
        planting_step = next((step for step in trace_chain if step['transaction_type'] == '种植'), None)
        harvest_step = next((step for step in trace_chain if step['transaction_type'] == '收获'), None)
        
        summary = {
            "product_lifecycle": f"{len(trace_chain)} 个关键步骤",
            "planting_date": planting_step['timestamp'] if planting_step else "未知",
            "harvest_date": harvest_step['timestamp'] if harvest_step else "未知",
            "quality_indicators": [],
            "certifications": ["区块链溯源认证"]
        }
        
        # 添加质量指标
        if harvest_step:
            harvest_data = harvest_step['data']
            if 'yield' in harvest_data:
                summary['quality_indicators'].append(f"产量: {harvest_data['yield']}")
            if 'quality_grade' in harvest_data:
                summary['quality_indicators'].append(f"质量等级: {harvest_data['quality_grade']}")
        
        return summary
    
    def _generate_certificate(self, product_id: str, verified: bool) -> Dict[str, Any]:
        """生成验证证书"""
        timestamp = datetime.now().isoformat()
        certificate_id = f"CERT_{product_id}_{int(datetime.now().timestamp())}"
        
        return {
            "certificate_id": certificate_id,
            "product_id": product_id,
            "issuer": "AI农业决策系统区块链",
            "issue_date": timestamp,
            "expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "verification_status": "已验证" if verified else "未验证",
            "verification_score": 0.95 if verified else 0.3,
            "qr_code_data": f"https://verify.agri-blockchain.com/{certificate_id}",
            "signature": hashlib.sha256(f"{certificate_id}{timestamp}".encode()).hexdigest()[:16]
        }


# 使用示例
if __name__ == "__main__":
    from datetime import timedelta
    
    blockchain = BlockchainSkill()
    
    # 记录种植信息
    planting_data = {
        "seed_variety": "超级稻1号",
        "planting_method": "机插",
        "density": "25万株/公顷",
        "soil_type": "黏土",
        "coordinates": "31.2304,121.4737"
    }
    
    planting_result = blockchain.record_planting(
        farm_id="farm_001",
        crop_id="rice_2024_001",
        planting_data=planting_data
    )
    print("种植记录:", json.dumps(planting_result, indent=2, ensure_ascii=False))
    
    # 记录施肥信息
    fertilization_data = {
        "fertilizer_type": "复合肥",
        "npk_ratio": "15-15-15",
        "amount_kg_per_ha": 300,
        "application_method": "撒施",
        "application_date": datetime.now().isoformat()
    }
    
    fertilization_result = blockchain.record_fertilization(
        farm_id="farm_001",
        crop_id="rice_2024_001",
        fertilizer_data=fertilization_data
    )
    print("\n施肥记录:", json.dumps(fertilization_result, indent=2, ensure_ascii=False))
    
    # 追溯产品
    trace_result = blockchain.trace_product("rice_2024_001")
    print("\n产品追溯:", json.dumps(trace_result, indent=2, ensure_ascii=False))
    
    # 验证产品
    verify_result = blockchain.verify_product("rice_2024_001")
    print("\n产品验证:", json.dumps(verify_result, indent=2, ensure_ascii=False))
    
    # 获取区块链统计
    stats = blockchain.get_blockchain_stats()
    print("\n区块链统计:", json.dumps(stats, indent=2, ensure_ascii=False))