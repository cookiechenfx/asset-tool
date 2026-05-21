import sys
from file_logger import FileLogger


class DataParser:
    def __init__(self, log=None):
        self.log = log
        if not self.log:
            self.log = FileLogger('logs', 'assetFormFiller')

    def parse_data_from_file(self, file_path, mode="资产变更"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_text = f.read()
                if "资产变更" in mode:
                    data = self.parse_asset_data(data_text)
                elif "部门调整" in mode:
                    data = self.parse_staff_data(data_text)
                return data
        except Exception as e:
            self.log.error(f"读取文件失败: {e}")
            sys.exit(1)

    def parse_asset_data(self, text_data):
        """
        解析制表符分隔的资产数据

        输入格式：
        使用人	部门	分类	操作类型	资产名称	资产编码	品牌型号	备注
        周明军	文创城法庭	其他	回收	台式计算机	510122MB1867896218000450	戴尔OptiPlex 3050 SFF 003068	文创城法庭	根据统一安排替换，从文创城法庭回收
        """
        lines = text_data.strip().split('\n')
        assets = []

        for line in lines:
            if not line.strip():
                continue

            # 按制表符分割
            parts = line.split('\t')
            if len(parts) >= 7:
                asset = {
                    'user': parts[0].strip(),  # 使用人
                    'department': parts[1].strip(),  # 部门
                    'reason': parts[2].strip(),  # 事由
                    'action': parts[3].strip(),  # 操作类型（回收/发放）
                    'name': parts[4].strip(),  # 资产名称
                    'asset_code': parts[5].strip(),  # 资产编码
                    'brand_model': parts[6].strip(),  # 品牌型号
                    'location':parts[7].strip() if len(parts) > 7 else '',  #地点
                    'remark': parts[8].strip() if len(parts) > 8 else '',  # 备注
                    'asset_type': parts[9].strip() if len(parts) > 9 else '固定资产'  #资产类型
                }
                assets.append(asset)

        return assets


    def parse_staff_data(self, text_data):
        lines = text_data.strip().split('\n')
        staffs = []

        for line in lines:
            if not line.strip():
                continue

            # 按制表符分割
            parts = line.split('\t')
            if len(parts) >= 3:
                staff = {
                    'user': parts[0].strip(),  # 使用人
                    'old_department': parts[1].strip(),  # 原部门
                    'new_department': parts[2].strip(),  # 新部门
                    'location': parts[3].strip() if len(parts) > 3 else ""
                }
                staffs.append(staff)

        return staffs
