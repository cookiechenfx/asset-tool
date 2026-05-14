import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from asset_form_filler import AssetFormFiller
import argparse
import sys


class AssetManagementSystem:
    def __init__(self, username, password, login_url):
        """初始化资产管理系统脚本"""
        self.username = username
        self.password = password
        self.login_url = login_url
        self.driver = None
        self.wait = None

        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        # 如果不使用debug模式，注释上一行，启用下一行
        # chrome_options.add_argument("--start-maximized")

        self.init_driver(chrome_options)

    def init_driver(self, chrome_options):
        """初始化浏览器驱动 - Ubuntu 版本"""
        try:
            chrome_options = Options()

            # 无头模式配置
            # chrome_options.add_argument('--headless')  # 无界面运行
            chrome_options.add_argument('--no-sandbox')  # 解决权限问题
            chrome_options.add_argument('--disable-dev-shm-usage')  # 解决资源限制
            chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速
            chrome_options.add_argument('--window-size=1920,1080')  # 设置窗口大小

            # 指定 Chromium 路径（Ubuntu 默认路径）
            chrome_options.binary_location = '/usr/bin/chromium-browser'

            # 指定 Chromedriver 路径
            service = Service('/usr/lib/chromium-browser/chromedriver')

            # 创建驱动
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 10)

            print("浏览器驱动初始化成功")
            return True
        except Exception as e:
            print(f"初始化失败: {e}")
            print("\n请确保已安装: sudo apt install chromium-browser chromium-chromedriver")
            return False

    def login(self):
        """登录系统"""
        try:
            self.driver.get(self.login_url)
            time.sleep(2)

            # 获取用户名和密码输入框（请根据实际情况修改选择器）
            password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")
            username_input = self.driver.find_element(By.XPATH, "//input[@type='text']")

            # 输入登录信息
            username_input.send_keys(self.username)
            password_input.send_keys(self.password)

            # 点击登录按钮
            login_btn = self.driver.find_element(By.XPATH, "//button[@type='button']")
            login_btn.click()

            time.sleep(3)
            print("登录成功")
            return True
        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def navigate_to_asset_list(self):
        """导航到资产列表页面"""
        try:
            print("\n正在导航到资产列表...")

            # 等待侧边栏加载
            time.sleep(2)

            # 方法1：先展开"资产管理"父菜单，再点击"资产列表"
            parent_title = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='el-submenu__title']//span[contains(text(), '资产管理')]/.."))
            )

            # 通过父菜单的兄弟元素查找
            parent_li = parent_title.find_element(By.XPATH, "./..")  # 找到li.el-submenu

            # 检查父菜单是否已展开（子菜单是否可见）
            sub_menu = parent_li.find_element(By.XPATH, "//ul[@role='menu']")

            # 如果子菜单是隐藏的，点击展开
            if sub_menu and 'display: none' in sub_menu.get_attribute('style'):
                # 点击父菜单展开
                self.driver.execute_script("arguments[0].click()", parent_li)
                print("✓ 已展开'资产管理'菜单")
                time.sleep(0.5)

            # 点击"资产列表"
            asset_list = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '资产列表')]"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", asset_list)
            time.sleep(0.5)
            asset_list.click()
            print("✓ 通过父菜单+子菜单方式点击资产列表")
            time.sleep(1)
            return True

        except Exception as e:
            print(f"✗ 导航失败: {e}")
            return False

    def search_asset(self, asset_code):
        """搜索资产 - 适配通用搜索框"""
        try:
            print(f"\n搜索资产: {asset_code}")
            # time.sleep(0.5)

            selector = "//input[@class='el-input__inner' and @placeholder='资产名称/编码/规格型号/供应商']"
            search_input = None
            try:
                search_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                # search_input = self.driver.find_element(By.XPATH, selector)
                print(f"✓ 找到搜索框: {selector}")
            except Exception as e:
                print(f"未找到搜索框: {e}")

            # 清空并输入资产编码
            search_input.clear()
            time.sleep(0.5)
            search_input.send_keys(asset_code)
            print(f"✓ 已输入搜索内容: {asset_code}")

            # 等待搜索建议或直接搜索
            time.sleep(1)

            # 查找查询按钮
            selector = "//div[contains(@class, 'el-input-group__append')]//button//i[@class='el-icon-search']/parent::button"
            btn_found = False
            try:
                query_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                query_btn.click()
                btn_found = True
                print("✓ 已点击查询按钮")
            except Exception as e:
                    print(f"未找到搜索按钮: {e}")

            if not btn_found:
                # 按回车搜索
                search_input.send_keys("\n")
                print("✓ 已按回车搜索")

            # 等待搜索结果加载
            time.sleep(3)

            # 等待表格或结果出现
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
                print("✓ 搜索结果已加载")
            except:
                print("⚠ 未检测到表格，但继续执行")

            return True

        except Exception as e:
            print(f"✗ 搜索资产失败: {e}")
            return False

    def select_asset(self, asset_code):
        """选中资产"""
        try:
            print(f"\n准备选中资产: {asset_code}")
            # time.sleep(2)

            row_selector = f"//td[contains(@class, 'el-table_1_column_4')]//div[text()='{asset_code}']/ancestor::tr"
            row = self.driver.find_element(By.XPATH, row_selector)
            print(f"✓ 找到资产所在行")

            checkbox_selector = f".//td[contains(@class, 'el-table_1_column_1')]//input[@type='checkbox']"
            try:
                elem = row.find_element(By.XPATH, checkbox_selector)
                self.driver.execute_script("arguments[0].click();", elem)
                print(f"✓ {asset_code}资产的选中复选框")
                time.sleep(0.5)
                return True
            except Exception as e:
                print(f"选中复选框失败：{e}")
                return False

        except Exception as e:
            print(f"✗ 选中资产失败: {e}")
            return False

    def modify_asset(self, modified_data):
        """修改固定资产台账"""
        asset_code = modified_data['asset_code']
        modified_mode = modified_data['action']
        try:
            # 搜索需要修改的资产
            if not self.search_asset(asset_code):
                print("无法找到指定资产")
                return False

            if not self.select_asset(asset_code):
                print("无法选中指定资产")
                return False

            time.sleep(2)

            # 点击操作按钮
            action_btn = None
            action_selector = "//button[contains(.,'操作')]"
            action_btn = self.driver.find_element(By.XPATH, action_selector)
            action_btn.click()
            time.sleep(1)

            if "发放" in modified_mode:
                    manage_selector = f"//li[contains(@class, 'el-dropdown-menu__item') and contains(., '领用')]"
            elif "回收" in modified_mode:
                manage_selector = f"//li[contains(@class, 'el-dropdown-menu__item') and contains(., '归还')]"
            elif "搬迁" in modified_mode:
                manage_selector = f"//li[contains(@class, 'el-dropdown-menu__item') and contains(., '变更')]"
            else:
                print(f"未知的调整模式：{modified_mode}")
                return False
            btn = self.driver.find_element(By.XPATH, manage_selector)
            btn.click()
            time.sleep(1)

            # 修改数据
            if "回收" in modified_mode:
                selector = f"//div[contains(@class, 'el-form-item')]//input[contains(@class, 'el-input__inner') and contains(@placeholder, '请输入或选择')]"
                # elem = self.driver.find_element(By.XPATH, selector)
                elem = None
                try:
                    elem = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print(f"✓ 找到地址输入框: {selector}")
                except Exception as e:
                    print(f"未找到地址输入框: {e}")

                if not elem:
                    print("✗ 未找到地址输入框")
                    return False

                # 清空并输入资产编码
                elem.clear()
                time.sleep(0.5)
                elem.send_keys(modified_data['location'])
                print(f"✓ 已填写内容: {modified_data['location']}")
                time.sleep(2)

                selector = f"//div[contains(@class,'dialog-footer')]//button[contains(., '确')]"
                btn = self.driver.find_element(By.XPATH, selector)

                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    print("✓ 资产变更信息已保存")
                    time.sleep(2)
                except:
                    return False

            elif "发放" in modified_mode:
                selector = (f"//div[contains(@class, 'el-form-item is-required') and contains(.,'领用人')]"
                            f"//button[contains(@class, 'el-button')]")
                btn = None
                try:
                    btn = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print(f"✓ 找到部门人员输入框: {selector}")
                    self.driver.execute_script("arguments[0].click();", btn)
                except Exception as e:
                    print(f"未找到部门人员输入框: {e}")

                if not btn:
                    print("✗ 未找到部门人员输入框")
                    return False

                # 搜索资产领用人员
                selector = (f"//div[contains(@class, 'el-dialog')]"
                            f"//input[contains(@class, 'el-input__inner') and contains(@placeholder, '搜索组织或员工')]")
                elem = None
                try:
                    elem = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print(f"✓ 找到部门人员搜索框: {selector}")
                    elem.clear()
                    time.sleep(0.5)
                    elem.send_keys(modified_data['user'])
                    print(f"✓ 已输入内容: {modified_data['user']}")
                    time.sleep(0.5)
                    elem.send_keys('\n')
                    time.sleep(1)
                except Exception as e:
                    print(f"未找到部门人员搜索框: {e}")

                if not elem:
                    print("✗ 未找到部门人员搜索框")
                    return False

                # 从搜索结果中选择部门人员信息
                tree_selector = f"//div[@role='tree']"
                # user_selector = (f"//div[contains(@class, 'el-tree-node__content')]"
                #                  f"/span[contains(@class, 'deptName') and normalize-space()='{modified_data['user']}'")
                user_selector = f"//span/span[contains(@class, 'deptName') and normalize-space()='{modified_data['user']}']"
                user_elems = None
                # department_selector = (f"//div[contains(@class, 'el-tree-node__content')]"
                #                        f"/span[contains(@class, 'deptName') and normalize-space()='{modified_data['department']}') and not(*)]")
                department_selector = f"//span/span[contains(@class, 'deptName') and normalize-space()='{modified_data['department']}']"
                try:
                    tree_elem = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, tree_selector))
                    )
                    user_elems = tree_elem.find_elements(By.XPATH, user_selector)
                    if len(user_elems) > 1:
                        department_elems = tree_elem.find_elements(By.XPATH, department_selector)
                        if len(department_elems) == 1:
                            group_elem = department_elems[0].find_elements(By.XPATH, "ancestor::div[contains(@class, 'el-tree-node') and @role='treeitem']")
                            user_elem = group_elem.find_element(By.XPATH, user_selector)
                        else:
                            print(f"找到多个同部门同姓名人员：{modified_data['department']}-{modified_data['user']}，请手动修改")
                    elif len(user_elems) == 1:
                        user_elem = user_elems[0]
                    else:
                        print(f"未找到人员：{modified_data['department']}-{modified_data['user']}")
                        return False

                except Exception as e:
                    print(f"未找到人员：{modified_data['department']}-{modified_data['user']}")

                time.sleep(0.5)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", user_elem)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", user_elem)
                time.sleep(1)

                btn_selector = (f"ancestor::div[@role='dialog']//div[@class='el-dialog__footer']"
                                f"//button[contains(@class, 'el-button--primary') and contains(., '确定')]")
                # btn = self.driver.find_element(By.XPATH, btn_selector)
                btn = tree_elem.find_element(By.XPATH, btn_selector)
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    print("✓ 已选择人员")
                    time.sleep(2)
                except:
                    return False
                # btn.click()

                # 清空并输入位置信息
                location_selector = f"//div[@class='el-form-item' and contains(., '存放地点')]//input[@class='el-input__inner' and @placeholder='请输入或选择']"
                location_elem = self.driver.find_element(By.XPATH, location_selector)
                location_elem.clear()
                time.sleep(0.5)
                location_elem.send_keys(modified_data['location'])
                print(f"✓ 已填写内容: {modified_data['location']}")
                time.sleep(2)

                btn_selector = f"//div[contains(@class,'dialog-footer')]//button[contains(., '确')]"
                btn = self.driver.find_element(By.XPATH, btn_selector)
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    print("✓ 资产变更信息已保存")
                    time.sleep(2)
                except:
                    return False

            elif "搬迁" in modified_mode:

                # 清空并输入位置信息
                location_selector = f"//div[@class='el-form-item' and contains(., '存放地点')]//input[@class='el-input__inner' and @placeholder='请输入或选择']"
                location_elem = self.driver.find_element(By.XPATH, location_selector)
                location_elem.clear()
                time.sleep(0.5)
                location_elem.send_keys(modified_data['location'])
                print(f"✓ 已填写内容: {modified_data['location']}")
                time.sleep(2)

                btn_selector = f"//div[contains(@class,'dialog-footer')]//button[contains(., '确')]"
                btn = self.driver.find_element(By.XPATH, btn_selector)
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    print("✓ 资产变更信息已保存")
                    time.sleep(2)
                except:
                    return False
            else:
                print(f"未知的调整模式：{modified_mode}")
                return False

            # for field, value in modified_data.items():
            #     try:
            #         input_element = self.driver.find_element(By.ID, field)
            #         input_element.clear()
            #         input_element.send_keys(value)
            #     except:
            #         print(f"未找到字段: {field}")
            #
            # # 保存修改
            # save_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), '保存')]")
            # save_btn.click()
            # time.sleep(2)

            print(f"资产 {asset_code} 修改成功")
            return True
        except Exception as e:
            print(f"修改资产失败: {e}")
            return False

    def batch_modify_assets(self, modification_list):
        """批量修改固定资产"""
        results = []
        for asset in modification_list:
            status = self.modify_asset(asset['asset_code'], asset['modified_data'])
            results.append({
                'asset_code': asset['asset_code'],
                'status': '成功' if status else '失败'
            })
            time.sleep(1)

        return results


    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")


def main():
    """主函数 - 使用示例"""
    """主函数"""
    parser = argparse.ArgumentParser(
        description='资产领用/回收单生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
        使用示例:
      # 直接传入制表符分隔的数据
      python asset_form.py "姓名\t部门\t事由\t发放/回收\t资产名称\t资产编码\t资产型号\t地点\t备注"

      # 传入多行数据（用引号包裹）
      python asset_form.py "姓名\t部门\t事由\t发放/回收\t资产名称\t资产编码1\t资产型号\t地点\t备注
    姓名\t部门\t事由\t发放/回收\t资产名称\t资产编码2\t资产型号\t地点\t备注"

      # 从文件读取数据
      python asset_form.py --file assets.txt

      # 指定输出文件名
      python asset_form.py --data "姓名\t部门\t事由\t发放/回收\t资产名称\t资产编码\t资产型号\t地点\t备注" --output 周明军_资产表单.xlsx
            '''
    )

    parser.add_argument('data', nargs='?', help='资产数据（制表符分隔）')
    parser.add_argument('--file', '-f',
                        default="./in_file.txt", help='从文件读取数据')
    parser.add_argument('--template-path', '-t',
                        default="./固定资产领用及回收单-模板.xlsx", help='指定模板文件')
    parser.add_argument('--output', '-o', help='输出文件名')
    parser.add_argument('--output-dir', '-d', default='forms', help='输出目录（默认: forms）')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    # 获取数据
    data_text = None

    if args.file:
        # 从文件读取
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                data_text = f.read()
            if args.verbose:
                print(f"✓ 从文件读取: {args.file}")
        except Exception as e:
            print(f"读取文件失败: {e}")
            sys.exit(1)
    elif args.data:
        # 从命令行参数读取
        data_text = args.data
        if args.verbose:
            print(f"✓ 从命令行读取数据")
    else:
        # 没有提供数据，显示帮助
        parser.print_help()
        sys.exit(1)

    if not data_text or not data_text.strip():
        print("错误：没有提供数据")
        sys.exit(1)

    filler = AssetFormFiller(template_path=args.template_path, output_dir=args.output_dir)
    print("\n正在解析数据...")
    assets = filler.parse_tab_data(data_text)
    print(f"✓ 成功解析 {len(assets)} 条资产记录")

    if not assets:
        print("错误：无法解析数据，请确保格式正确（使用制表符分隔）")
        print("格式：使用人\t部门\t分类\t操作类型\t资产名称\t资产编码\t品牌型号\t备注")
        sys.exit(1)

    if args.verbose:
        print(f"✓ 解析到 {len(assets)} 条资产记录")
        for i, asset in enumerate(assets, 1):
            print(f"  {i}. {asset['name']} - {asset['action']} - {asset['user']}")

        # 配置信息
    config = {
        'username': '13683498313',  # 替换为您的用户名
        'password': 'tfxxhzcgl619%',  # 替换为您的密码
        'login_url': 'https://gz.dothantech.com/#/login'  # 替换为您的系统登录地址
    }

    # 初始化系统
    ams = AssetManagementSystem(config['username'], config['password'], config['login_url'])

    try:
        # 登录
        if not ams.login():
            print("登录失败，程序退出")
            return

        """
        asset = {
                    'user': '张三',  # 使用人
                    'department': '综合办（法警大队）',  # 部门
                    'reason': '离职',  # 事由
                    'action': '回收',  # 操作类型（回收/发放）
                    'name': '台式计算机',  # 资产名称
                    'asset_code': 'testTY2020000059',  # 资产编码
                    'brand_model': '戴尔**',  # 品牌型号
                    'location': '2号楼630',  #地点
                    'remark': '电话号码2000',  # 备注
                    'asset_type': '固定资产'  #资产类型
                }
        """

        ams.navigate_to_asset_list()
        for asset in assets:
            ams.modify_asset(asset)

        # # 示例2：批量修改资产
        # modifications = [
        #     {
        #         'asset_code': 'ASSET001',
        #         'modified_data': {'user': '张三', 'location': 'A栋301室'}
        #     },
        #     {
        #         'asset_code': 'ASSET002',
        #         'modified_data': {'user': '李四', 'location': 'B栋202室'}
        #     }
        # ]
        # results = ams.batch_modify_assets(modifications)
        # print("批量修改结果:", results)

        # 示例3：生成领用单
        asset_info = {
            'form_no': 'GD20231201001',
            'apply_date': '2023-12-01',
            'department': '信息技术部',
            'applicant': '王五',
            'asset_code': 'CP-2023-001',
            'asset_name': '笔记本电脑',
            'model': 'ThinkPad X1 Carbon',
            'purchase_date': '2023-06-01',
            'original_value': '12,000.00',
            'depreciation': '500.00',
            'status': '领用中',
            'location': 'A栋1001室',
            'remarks': '办公使用'
        }

        # 生成领用单
        # receive_form = ams.generate_recovery_form(asset_info, 'receive')

        # # 生成回收单
        # asset_info['remarks'] = '设备更新，原设备回收'
        # recovery_form = ams.generate_recovery_form(asset_info, 'recovery')

        # 示例4：导出现有资产列表
        # ams.export_asset_list({'department': '信息技术部'})

    except Exception as e:
        print(f"程序运行出错: {e}")

    finally:
        # 关闭浏览器
        ams.close()

    # 按使用人分组
    grouped = filler.group_assets_by_user(assets)

    if args.verbose:
        print(f"\n✓ 分组为 {len(grouped)} 个表单")

    # 为每个使用人生成表单
    results = []
    for user_key, group in grouped.items():
        if args.verbose:
            print(f"\n为{group['asset_type']} {group['user']} ({group['department']}) 生成表单...")
        output_file = filler.fill_form(group)
        if output_file:
            results.append(output_file)
            # print(f"  ✓ 表单已保存: {output_file}")

    if not args.verbose:
        # print("\n" + "=" * 60)
        print(f"\n✓ 成功生成 {len(results)} 个表单")
        for f in results:
            print(f"  - {f}")




# 使用配置文件的方式
def load_config():
    """从配置文件加载系统配置"""
    config_file = 'asset_config.json'
    import json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("配置文件不存在，创建默认配置...")
        default_config = {
            "username": "your_username",
            "password": "your_password",
            "login_url": "http://your-system-url/login",
            "chrome_driver_path": "chromedriver.exe"
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"请填写配置文件 {config_file} 后再运行")
        return None


if __name__ == "__main__":
    # 方式1：直接运行
    main()

    # 方式2：从配置文件加载
    # config = load_config()
    # if config:
    #     ams = AssetManagementSystem(
    #         config['username'],
    #         config['password'],
    #         config['login_url']
    #     )
    #     # ... 后续操作
