import requests
from datetime import datetime
import sys
import json

from data_parser import DataParser
from asset_form_filler import AssetFormFiller
from file_logger import FileLogger

CODE_SUCCESS = 0      # 成功状态码

# ===================== 核心自动化流程 =====================
class AssetAutomator:
    def __init__(self, base_url, headers, username, password, log):
        self.base_url = base_url
        self.HEADERS = headers
        self.phoneNumber = username
        self.password = password
        self.log = log
        self.loginID = ""
        self.id = ""
        self.name = "管理员"
        self.departmentList = None
        self.staffList = None

        # 创建会话：自动保存登录Cookie，全程保持登录状态
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.login()
        self.get_department_list()
        self.get_staff_list()

    def login(self):
        """登录"""
        # print("🔐 正在登录...")
        self.log.debug(f"正在登录资产管理系统：账号{self.phoneNumber}，登录密码{self.password}")
        login_info = {
            "phoneNumber": self.phoneNumber,
            "password": self.password  #"5D470E15CD8DD9C813B9555DC7FD0DA9"
            }
        try:
            res = self.session.post(f"{self.base_url}/api/login",
                                    json=login_info)

            result = res.json()
            if result.get("statusCode") == CODE_SUCCESS:
                # print("✅ 登录成功！")
                self.log.info("✅ 资产管理系统登录成功")
                self.loginID = result.get("resultInfo").get("loginID")
                self.id = result.get("resultInfo").get("id")
                return True
            else:
                # print(f"❌ 登录失败：{result}")
                self.log.error(f"❌ 资产管理系统登录失败{result}")
                return False
        except Exception as e:
            self.log.error(f"❌ 请求异常：{e}")
            # print("请求异常：", e)

    def get_department_list(self):
        res = self.session.get(f"{self.base_url}/api/Department/List",
                               params={
                                   'loginID': self.loginID,
                                   'systemFlag': "MYGDZC"
                               })
        result = res.json()
        if result.get('statusCode') == CODE_SUCCESS:
            self.departmentList = result.get('resultInfo').get('departments')
            # print(f"共查询到{len(self.departmentList)}个部门")
            self.log.debug(f"✅ 共查询到{len(self.departmentList)}个部门")
            return True
        else:
            # print("未查询到部门信息")
            self.log.warning("❌ 未查询到部门信息")
            return False

    def get_staff_list(self):
        res = self.session.get(f"{self.base_url}/api/Staff/List",
                               params={
                                   'loginID': self.loginID,
                                   'systemFlag': "MYGDZC"
                               })
        result = res.json()
        if result.get('statusCode') == CODE_SUCCESS:
            self.staffList = result.get('resultInfo').get('staffs')
            # print(f"共查询到{len(self.staffList)}个人员")
            self.log.debug(f"✅ 共查询到{len(self.staffList)}个人员")
            return True
        else:
            # print("未查询到人员信息")
            self.log.warning("❌ 未查询到人员信息")
            return False

    def check_department_staff(self, department, staff):

        if department and staff:
            if staff.get('affiliatedDept') == department.get('id'):
                return True
        return False

    def search_staffs(self, staff_name):
        right_staffs = []
        if len(staff_name) > 0:
            for idx, item in enumerate(self.staffList):
                if staff_name == item.get('staffName'):
                    right_staffs.append(item)
            if len(right_staffs) > 0:
                self.log.debug(f"找到名称为 {staff_name} 的部门 {len(staff_name)} 个")
                return right_staffs

        self.log.warning(f"人员:{staff_name}不存在")
        return None

    def search_staff(self, staff_name):
        right_staffs = self.search_staffs(staff_name)
        if len(right_staffs) > 0:
            if len(right_staffs) > 1:
                self.log.warning(f"找到名称为 {right_staffs} 的员工 {len(right_staffs)} 个，返回第一个")
            return right_staffs[0]
        return None

    def search_departments(self, departmentName):
        right_departments = []
        if len(departmentName) > 0:
            for idx, item in enumerate(self.departmentList):
                if departmentName == item.get('deptName'):
                    right_departments.append(item)
            if len(right_departments) > 0:
                self.log.debug(f"找到名称为 {departmentName} 的部门 {len(right_departments)} 个")
                return right_departments

        self.log.warning(f"部门:{departmentName}不存在")
        return None

    def search_department(self, departmentName):
        right_departments = self.search_departments(departmentName)
        if len(right_departments) > 0:
            if len(right_departments) > 1:
                self.log.warning(f"找到名称为 {departmentName} 的部门 {len(right_departments)} 个，返回第一个")
            return right_departments[0]
        return None

    def search_department_staff(self, departmentName, staffName):
        if not departmentName or not staffName:
            self.log.error(f"未输入完整的信息，无法查找 - 部门:{departmentName} 人员：{staffName}")
            return None

        right_departments = self.search_departments(departmentName)

        right_staffs = []
        for idx, item in enumerate(self.staffList):
            if staffName == item.get('staffName'):
                for idx_d, item_d in enumerate(right_departments):
                    if item.get('affiliatedDept') == item_d.get('id'):
                        right_staffs.append(item)
        if len(right_staffs) > 0:
            if len(right_staffs) > 1:
                self.log.warning(f"找到名称为 {staffName} 的部门 {len(staffName)} 个, 返回第一个人员信息")
            return right_staffs[0]

        self.log.warning(f"部门:{departmentName} 人员：{staffName}不存在")
        return None

    def create_staff_account_by_name(self, departmentName, staffName):
        if not departmentName or not staffName:
            self.log.error(f"新建用户失败！需同时输入部门:{departmentName}人员:{staffName}信息")
            return False
        department = self.search_department(departmentName)
        if department:
            id = department.get('id', "")
        else:
            self.log.error(f"❌ 新建用户失败！未知的部门:{departmentName}")
            return False
        if id and staffName:
            params = {
                'affiliatedDept': id,
                'id': "",
                'jobNumber': "",
                'position': "",
                'staffName': staffName
            }
            res = self.session.post(f"{self.base_url}/api/Staff",
                                    json=params,
                                    params={'loginID': self.loginID})

            result = res.json()
            if result.get('statusCode') == CODE_SUCCESS:
                self.log.info(f"新建用户成功，部门：{department.get('deptName')} 姓名：{staffName}")
                flag_update_staff_list = self.get_staff_list()
                if not flag_update_staff_list:
                    self.log.warning("人员列表未正常更新！！！")
                return True
            else:
                self.log.error("新建用户失败！")
                return False
        else:
            self.log.error("未知的部门，新建用户失败！")
            return False

    def delete_staff_account_by_name(self, department_name, staff_name):
        if not department_name or not staff_name:
            self.log.error(f"新建用户失败！需同时输入部门:{department_name}人员:{staff_name}信息")
            return False
        staff = self.search_department_staff(department_name, staff_name)
        return self.delete_staff_account(staff)


    def delete_staff_account(self, staff):
        if not staff:
            self.log.warning(f"待删除用户不存在")
            return False
        if staff:
            params = {
                'affiliatedDept': staff.get('affiliatedDept', ""),
                'id': staff.get('id', ""),
                'staffName': staff.get('staffName', ""),
                'userID': self.id,
                'jobNumber': "",
                'position': "",
                'workingPosition': 1,
                'loginID': self.loginID
            }
            res = self.session.delete(f"{self.base_url}/api/Staff",
                                    params=params)

            result = res.json()
            if result.get('statusCode') == CODE_SUCCESS:
                self.log.info(f"✅ 用户 {staff.get('staffName')} 删除成功")
                flag_update_staff_list = self.get_staff_list()
                if not flag_update_staff_list:
                    self.log.warning("人员列表未正常更新！！！")
                return True
            else:
                self.log.error("用户 {staff.get('staffName')} 删除失败！")
                return False

        self.log.warning("未找到待删除用户！")
        return False

    def query_asset_by_code(self, asset_code):
        """根据资产编码查询目标资产，返回资产"""
        if not asset_code:
            self.log.warning(f"无法查询-请输入资产编码")
            return None

        query_condition = {
            "location": "0",
            "length": "50",
            "isASC": "false",
            "sortKey": "id,updateTime",
            "searchValue": asset_code,
            "filterStatus": "0",
            "filterDept": "",
            "filterStaff": "",
            "filterDepositSite": "",
            "filterExpireDateBegin": "",
            "filterExpireDateEnd": "",
            "filterBuyDateBegin": "",
            "filterBuyDateEnd": "",
            "filterAssetClassify": "",
            "filterSupplier": "",
            "filterDtptName":  "",
            "filterStaffName":  "",
            "loginID": self.loginID
        }

        res = self.session.get(f"{self.base_url}/api/asset",
                               params=query_condition)
        result = res.json()

        if result.get("statusCode") != CODE_SUCCESS:
            self.log.warning(f"❌ 查询失败：{result}")
            return None

        asset_list = result.get("resultInfo").get("assets", [])
        if len(asset_list) == 1:
            asset = asset_list[0]
            self.log.info(f"✅ 查询到资产：编码={asset.get('assetCoding')}, 名称={asset.get('assetName')}")
            return asset
        elif len(asset_list) > 1:
            for asset in asset_list:
                if asset['assetCoding'] == asset_code:
                    self.log.info(f"✅ 查询到资产：编码={asset.get('assetCoding')}, 名称={asset.get('assetName')}")
                    return asset
        else:
            self.log.warning("❌ 未查询到符合条件的资产")
            return None

    def query_asset_by_department_and_staff(self, departmentName, staffName):
        """根据部门和人员查询目标资产，返回资产"""
        if not departmentName or not staffName:
            self.log.error(f"无法查询-请输入完整的部门人员信息: 部门：{departmentName} 人员：{staffName}")
            return None
        searched_staff = self.search_department_staff(departmentName, staffName)
        if searched_staff:
            self.log.debug(f"✅ 查询到已有部门人员信息:{departmentName} {staffName}")
        else:
            self.log.warning(f"❌ 未查询到部门人员:{departmentName} {staffName}，请确认或新建账号")
            return None

        query_condition = {
            "location": "0",
            "length": "50",
            "isASC": "false",
            "sortKey": "updateTime",
            "searchValue": "",
            "filterStatus": "0",
            "filterDept": searched_staff.get('affiliatedDept', ""),
            "filterStaff": searched_staff.get('id', ""),
            "filterDepositSite": "",
            "filterExpireDateBegin": "",
            "filterExpireDateEnd": "",
            "filterBuyDateBegin": "",
            "filterBuyDateEnd": "",
            "filterAssetClassify": "",
            "filterSupplier": "",
            "filterDtptName": departmentName,
            "filterStaffName": searched_staff.get('staffName', ""),
            "loginID": self.loginID
        }

        res = self.session.get(f"{self.base_url}/api/asset",
                               params=query_condition)
        result = res.json()

        if result.get("statusCode") != CODE_SUCCESS:
            self.log.warning(f"❌ 查询失败：{result}")
            return None

        asset_list = result.get("resultInfo").get("assets", [])
        if len(asset_list) > 0:
            self.log.info(f"✅ 查询到 {departmentName} {staffName} 名下总共 {len(asset_list)} 条资产信息！！")
            return asset_list
        else:
            self.log.warning("❌ 未查询到符合条件的资产")
            return None

    def update_remark(self, asset):
        new_asset = self.query_asset_by_code(asset_code=asset['asset_code'])
        remark = asset.get('remark', "")
        if not remark:
            self.log.warning("备注内容为空，无需修改备注")
            return
        attributes = {
            "备注": remark
        }
        str_attributes= json.dumps(attributes, ensure_ascii=False, separators=(',', ':'))
        operate_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {
            "id": new_asset.get('id', ""),
            "assetCoding": new_asset.get('assetCoding', ""),
            "assetName": new_asset.get('assetName', ""),
            "assetClassify": new_asset.get('assetClassify', ""),
            "specifications": new_asset.get('specifications', ""),
            "unit": new_asset.get('unit', ""),
            "buyDate": new_asset.get('buyDate', ""),
            "buyPrice": json.dumps(new_asset.get('buyPrice', ""), ensure_ascii=False),
            "lossCycle": json.dumps(new_asset.get('lossCycle', ""), ensure_ascii=False),
            "supplier": new_asset.get('supplier', ""),
            "affiliatedDept": new_asset.get('affiliatedDept', ""),
            "affiliatedStaff": new_asset.get('affiliatedStaff', ""),
            "depositSite": new_asset.get('depositSite', ""),
            "attributeValues": str_attributes,
            "EPC": new_asset.get('EPC', ""),
            "TID": new_asset.get('TID', ""),
            "status": "4",
            "expireDate": new_asset.get('expireDate', ""),
            "updateTime": operate_time,
            "state": "0"
        }

        remark_res = self.session.post(f"{self.base_url}/api/asset",
                                      data=data,
                                      params={'loginID': self.loginID})
        remark_result = remark_res.json()
        if remark_result.get("statusCode") == CODE_SUCCESS:
            self.log.info(f"✅ {new_asset['assetName']} {new_asset['assetCoding']} 备注内容：{remark} 修改成功！")
        else:
            self.log.error(f"备注：{remark} 未修改！！！！")
        return

    def update_asset_by_code(self, asset):
        """根据资产编码索引资产并修改资产信息"""
        asset_code = asset.get('asset_code', "")
        department_name = asset.get('department', "")
        staff_name = asset.get('user', "")
        location = asset.get('location', "")
        action = asset.get('action', "")
        asset_name = asset.get('name', "")
        remark = asset.get('remark', "")

        searched_asset = self.query_asset_by_code(asset_code=asset_code)
        if searched_asset:
            asset_id = searched_asset.get('id')
        else:
            self.log.error(f"❌ 未查询到准确的资产信息，资产{asset_code}修改失败")
            return

        # 判断是否已有部门的人员，如果不是则新建账号
        if "发放" in asset['action']:
            searched_staff = self.search_department_staff(departmentName=department_name, staffName=staff_name)
            if not searched_staff:
                flag_created = self.create_staff_account_by_name(departmentName=department_name, staffName=staff_name)
                if not flag_created:
                    self.log.error(f"❌ 未查询到人员且无法创建，资产编码{asset_code}修改失败")
                    return

        self.log.debug("正在修改资产")

        # 自动把查询到的资产ID填入修改数据
        operate_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        condition_json = {
            'assetNumbers': asset_id,
            'id': "",
            'loginFlag': 1,
            'operateTime': operate_time,
            'operatorID': self.id,
            'operatorName': self.name
            }

        if "发放" in action or "变更" in action:
            condition_json.update({
                'businessStatus':2,
                'deptName': department_name,
                'staffName': staff_name,
                'depositSite': location
            })
        elif "回收" in action:
            condition_json.update({
                'businessStatus': 64,
                'depositSite': location
            })
        elif "搬迁" in action:
            condition_json.update({
                'businessStatus': 2,
                'depositSite': location
            })
        else:
            self.log.error(f"未知的修改方式:{action}，无法修改资产{asset_id}")
            return False

        res = self.session.post(f"{self.base_url}/api/Business",
                                json=condition_json,
                                params={ 'loginID': self.loginID}
                                )
        result = res.json()

        if result.get("statusCode") == CODE_SUCCESS:
            result_info = result.get('resultInfo')
            if  result_info and "座机" in asset_name and remark:
                self.update_remark(asset)
            self.log.info(f"✅ 📊资产修改完成,  修改后数据：{result_info}")
        else:
            self.log.error(f"❌ 修改失败：{result}")
        return result

    def batch_update_assets_by_code(self, asset_list):
        results = []
        for asset in asset_list:
            result = self.update_asset_by_code(asset)
            results.append(result)
        return results

    def update_department(self, data):
        user_name = data['user']
        old_department_name = data['old_department']
        new_department_name = data['new_department']
        location = data['location']
        old_staff = self.search_department_staff(old_department_name, user_name)
        # 新建新部门的人员账号
        new_staff = self.search_department_staff(new_department_name, user_name)
        if not new_staff:
            new_staff = self.create_staff_account_by_name(departmentName=new_department_name, staffName=user_name)
            if not new_staff:
                self.log.error(f"新建部门{new_department_name}人员{user_name}账号失败，无法调整部门")

        asset_list = self.query_asset_by_department_and_staff(departmentName=old_department_name, staffName=user_name)

        results = []
        if asset_list and new_staff:
            for asset in asset_list:
                input_asset = {
                    'asset_code': asset['assetCoding'],
                    'department': new_department_name,
                    'user': user_name,
                    'name': asset['assetName'],
                    'location': location if location else asset['depositSite'],
                    'action': "变更"
                }
                result = self.update_asset_by_code(input_asset)
                results.append(result)

        self.delete_staff_account(old_staff)
        return results

    def batch_update_department(self, data_list):
        results = []
        for data in data_list:
            # print(asset)
            result = self.update_department(data)
            results.append(result)
        return results


    def run(self):
        """执行完整流程"""
        asset_id = self.query_asset()
        self.update_asset(asset_id)

def main():
    """ 生成log文件 """

    params = load_param_from_json()
    log = FileLogger("logs", "assetAutomator", level=params.get('log_level', 20))
    log.info("程序启动")

    log.info(f"从 {params['in_file_path']} 中解析数据")
    data_parser = DataParser(log=log)
    data_list = data_parser.parse_data_from_file(params['in_file_path'], params['mode'])
    if type(data_list) == list and len(data_list) > 0:
        log.info(f"成功解析 {len(data_list)} 条记录")
    else:
        log.error("错误：无法解析数据，请确保格式正确（使用制表符分隔）")
        sys.exit(1)

    # 初始化系统
    ams = AssetAutomator(
        params['base_url'],
        params['HEADERS'],
        params['username'],
        params['encrypted_password'],
        log.get_logger()
    )

    # 批量修改资产信息
    if "部门调整" in params['mode']:
        for i, data in enumerate(data_list):
            log.info(f"人员{i}. {data['user']} - {data['old_department']} - {data['new_department']} - {data['location']}")
        ams.batch_update_department(data_list)
    elif "资产变更" in params['mode']:
        for i, asset in enumerate(data_list):
            log.info(f"资产{i}. {asset['name']} - {asset['asset_code']} - {asset['action']} - {asset['user']}")
        ams.batch_update_assets_by_code(data_list)

        # 生成资产申领单
        filler = AssetFormFiller(params['template_path'], params['output_dir'], log.get_logger())
        filler.fill_forms(data_list)



# 使用配置文件的方式
def load_param_from_json():
    """从配置文件加载系统配置"""
    config_file = './assetAutomator_config.json'
    import json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"请创建配置文件 {config_file} 后再运行")
        return None



# ===================== 启动程序 =====================
if __name__ == "__main__":
    main()
