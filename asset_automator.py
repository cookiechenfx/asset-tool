import requests
from datetime import datetime
import sys
from asset_form_filler import AssetFormFiller
import json
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
                self.adminID = result.get("resultInfo").get("id")
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
            self.log.warning("未查询到部门信息")
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
            self.log.debug(f"共查询到{len(self.staffList)}个人员")
            return True
        else:
            # print("未查询到人员信息")
            self.log.warning("未查询到人员信息")
            return False

    def check_department_staff(self, departmentName="", staffName=""):
        if not staffName and not departmentName:
            self.log.warning("未输入部门、人员信息")
            return False

        right_staff = None
        right_department = None
        if len(staffName) > 0:
            right_staff = self.search_staff(staffName)

        if len(departmentName) > 0:
            right_department = self.search_department(departmentName)

        if right_staff and right_department:
            if right_staff.get('affiliatedDept') == right_department.get('id'):
                return True

        return False


    def search_staff(self, staffName):
        right_staff = None
        if len(staffName) > 0:
            id_staff = -1
            for idx, item in enumerate(self.staffList):
                if staffName == item.get('staffName'):
                    id_staff = idx
                    break
            if id_staff >= 0 and id_staff < len(self.staffList):
                right_staff = self.staffList[id_staff]
            else:
                self.log.warning(f"人员:{staffName}不存在")
                return False
                # print(right_staff)

        return right_staff

    def search_department(self, departmentName):
        right_department = None
        if len(departmentName) > 0:
            id_department = -1
            for idx, item in enumerate(self.departmentList):
                if departmentName == item.get('deptName'):
                    id_department = idx
                    break
            if id_department >= 0 and id_department < len(self.departmentList):
                right_department = self.departmentList[id_department]
            else:
                self.log.warning(f"部门:{departmentName}不存在")

        return right_department


    def create_staff_account(self, departmentName, staffName):
        department = self.search_department(departmentName )
        id = department.get('id', "")
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
                return True
            else:
                self.log.error("新建用户失败！")
                return False
        else:
            self.log.error("未知的部门，新建用户失败！")
            return False


    def query_asset(self, asset_code="", department="", user=""):
        """查询目标资产，返回资产"""
        if asset_code:
            department = ""
            user = ""
        else:
            flag_right = self.check_department_staff(department, user)
            if flag_right:
                self.log.info(f"🔍 查询到已有部门\人员信息:{department} {user}")
            else:
                self.log.warning(f"🔍 未查询到部门人员:{department} {user}，请确认或新建账号")
                return None

        if not asset_code and not flag_right:
            self.log.warning(f"无法查询-请输入准确的资产编码或部门人员信息: 资产编码：{asset_code} 部门：{department} 人员：{user}")
            return None

        # print(asset)
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
            "filterDtptName": department,
            "filterStaffName": user,
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
            self.log.info(f"查询到{len(asset_list)}条资产信息！！")
            return asset_list
        else:
            self.log.warning("❌ 未查询到符合条件的资产")
            return None

    def update_remark(self, asset):
        new_asset = self.query_asset(asset_code=asset['asset_code'])
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
            self.log.info(f"✅ {new_asset['assetName']} {new_asset['assetCoding']} 备注内容：{remark}修改成功！")
        else:
            self.log.error(f"备注{remark}未修改！！！！")
        return


    def update_asset(self, asset):
        """修改资产信息"""
        searched_asset = self.query_asset(asset_code=asset['asset_code'])
        # print(searched_asset)
        asset_id = searched_asset.get('id')
        if not asset_id:
            return
        if "发放" in asset['action'] or "调整" in asset['action']:
            flag_checked = self.check_department_staff(departmentName=asset['department'], staffName=asset['user'])
            if not flag_checked:
                flag_created = self.create_staff_account(departmentName=asset['department'], staffName=asset['user'])
                if not flag_created:
                    return

        self.log.debug("正在修改资产")
        action = asset['action']
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

        if "发放" in action :
            condition_json.update({
                'businessStatus':2,
                'deptName': asset['department'],
                'staffName': asset['user'],
                'depositSite': asset['location']
            })
        elif "回收" in action:
            condition_json.update({
                'businessStatus': 64,
                'depositSite': asset['location']
            })
        elif "搬迁" in action:
            condition_json.update({
                'businessStatus': 2,
                'depositSite': asset['location']
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
            if "座机" in asset['name']:
                self.update_remark(asset)
            self.log.info(f"✅ 📊资产修改完成,  修改后数据：{result.get('resultInfo')}")
        else:
            self.log.error(f"❌ 修改失败：{result}")
        return result

    def batch_update_assets(self, asset_list):
        results = []
        for asset in asset_list:
            # print(asset)
            result = self.update_asset(asset)
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

    filler = AssetFormFiller(params['template_path'], params['output_dir'], log.get_logger())
    log.debug("解析数据")
    assets = filler.parse_data_from_file(params['in_file_path'])
    log.info(f"成功解析 {len(assets)} 条资产记录")

    if not assets:
        log.error("错误：无法解析数据，请确保格式正确（使用制表符分隔）")
        sys.exit(1)

    for i, asset in enumerate(assets):
        log.info(f"资产{i}. {asset['name']} - {asset['asset_code']} - {asset['action']} - {asset['user']}")

    # 初始化系统
    ams = AssetAutomator(
        params['base_url'],
        params['HEADERS'],
        params['username'],
        params['encrypted_password'],
        log.get_logger()
    )

    # 批量修改资产信息
    ams.batch_update_assets(assets)

    # 生成资产申领单
    filler.fill_forms(assets)


# 使用配置文件的方式
def load_param_from_json():
    """从配置文件加载系统配置"""
    config_file = './assetAutomator_config.json'
    import json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # print(config)
        return config
    except FileNotFoundError:
        print(f"请创建配置文件 {config_file} 后再运行")
        return None


# ===================== 启动程序 =====================
if __name__ == "__main__":
    main()
