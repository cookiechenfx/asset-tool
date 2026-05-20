import time
import argparse
import sys

from asset_form_filler import AssetFormFiller
from asset_management_system import AssetManagementSystem
from asset_automator import AssetAutomator


def main():
    """主函数 - 使用示例"""
    """主函数"""

    params = load_param_from_json()
    verbose = params['verbose']

    filler = AssetFormFiller(params['template_path'], params['output_dir'])
    print("\n正在解析数据...")
    assets = filler.parse_data_from_file(params['in_file_path'])
    print(f"✓ 成功解析 {len(assets)} 条资产记录")

    if not assets:
        print("错误：无法解析数据，请确保格式正确（使用制表符分隔）")
        sys.exit(1)

    if verbose:
        print(f"✓ 解析到 {len(assets)} 条资产记录")
        for i, asset in enumerate(assets, 1):
            print(f"  {i}. {asset['name']} - {asset['asset_code']} - {asset['action']} - {asset['user']}")

    # 初始化系统
    ams = AssetManagementSystem(
        params['username'],
        params['password'],
        params['login_url']
    )

    try:
        # 登录
        if not ams.login():
            print("登录失败，程序退出")
            return

        if not ams.navigate_to_asset_list():
            print("资产列表未正常打开，程序退出")
            return

        # for asset in assets:
        #     ams.modify_asset(asset)
        results = ams.batch_modify_assets(assets)
        print(f"资产修改结果如下：{results}")

    except Exception as e:
        print(f"程序运行出错: {e}")

    finally:
        # 关闭浏览器
        ams.close()

    # 生成资产申领单
    filler.fill_forms(assets)


# 使用配置文件的方式
def load_param_from_json():
    """从配置文件加载系统配置"""
    config_file = './asset_config.json'
    import json
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # print(config)
        return config
    except FileNotFoundError:
        print(f"请创建配置文件 {config_file} 后再运行")
        return None


def load_param_from_parse():
    parser = argparse.ArgumentParser(
        description='资产领用/回收单生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
            使用示例:
          # 从文件读取数据
          python asset_form.py --file assets.txt

          # 指定输出文件名
          python asset_form.py --file assets.txt --output 周明军_资产表单.xlsx
                '''
    )
    parser.add_argument('--file', '-f',
                        default="./in_file.txt", help='从文件读取数据')
    parser.add_argument('--template-path', '-t',
                        default="./固定资产领用及回收单-模板.xlsx", help='指定模板文件')
    parser.add_argument('--output', '-o', help='输出文件名')
    parser.add_argument('--output-dir', '-d', default='资产申领回收单', help='输出目录（默认: forms）')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    params = {
        'in_file': args.file,
        'output_dir': args.output_dir,
        'template_path': args.template_path,
        'verbose': args.verbose
    }
    return params


if __name__ == "__main__":
    main()
