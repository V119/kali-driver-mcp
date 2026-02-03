"""
MCP 客户端示例 - 连接到 kali-driver-mcp 服务

这个脚本演示了如何在其他 Python 项目中使用 kali-driver-mcp 服务。

使用方法：
1. 安装依赖: uv add mcp 或 pip install mcp
2. 修改下面的配置路径
3. 运行: python mcp_client_example.py
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ============================================================================
# 配置区域 - 请根据你的环境修改
# ============================================================================

# MCP 服务器路径配置
MCP_SERVER_PATH = "/完整路径/kali-driver-mcp"  # 修改为你的路径
CONFIG_FILE = f"{MCP_SERVER_PATH}/config.yaml"


# ============================================================================
# MCP 客户端封装类
# ============================================================================

class KaliDriverMCPClient:
    """Kali Driver MCP 客户端封装."""

    def __init__(self, server_path: str, config_file: str):
        """
        初始化客户端.

        Args:
            server_path: MCP 服务器代码路径
            config_file: 配置文件路径
        """
        self.server_params = StdioServerParameters(
            command="uv",
            args=[
                "run",
                "python",
                "-m",
                "kali_driver_mcp.server",
                "--config",
                config_file
            ],
            cwd=server_path
        )
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        """异步上下文管理器入口."""
        self.client = stdio_client(self.server_params)
        self.streams = await self.client.__aenter__()
        read, write = self.streams

        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出."""
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具.

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            工具返回的结果（JSON 解析后）
        """
        if not self.session:
            raise RuntimeError("Client not connected")

        result = await self.session.call_tool(name, arguments)
        return json.loads(result.content[0].text)

    async def list_tools(self):
        """列出所有可用工具."""
        if not self.session:
            raise RuntimeError("Client not connected")

        tools = await self.session.list_tools()
        return tools.tools


# ============================================================================
# 高级功能封装
# ============================================================================

class DriverDebugger:
    """驱动调试助手."""

    def __init__(self, client: KaliDriverMCPClient):
        self.client = client

    async def check_environment(self) -> Dict[str, Any]:
        """检查开发环境是否就绪."""
        print("🔍 检查开发环境...")

        results = {
            "kernel": None,
            "shared_folder": None,
            "network": None,
            "ready": False
        }

        try:
            # 检查内核信息
            print("  - 检查内核版本...")
            results["kernel"] = await self.client.call_tool(
                "kernel_info",
                {"detail_level": "basic"}
            )

            # 检查共享文件夹
            print("  - 检查共享文件夹...")
            results["shared_folder"] = await self.client.call_tool(
                "code_sync",
                {}
            )

            # 检查网络接口
            print("  - 检查网络接口...")
            results["network"] = await self.client.call_tool(
                "network_info",
                {"interface": "all", "detail_level": "basic"}
            )

            # 判断是否就绪
            results["ready"] = (
                results["kernel"] and
                results["shared_folder"].get("ready", False)
            )

            if results["ready"]:
                print("✅ 环境检查通过\n")
            else:
                print("⚠️  环境存在问题\n")

        except Exception as e:
            print(f"❌ 环境检查失败: {e}\n")
            results["error"] = str(e)

        return results

    async def compile_driver(
        self,
        clean: bool = False,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        编译驱动.

        Args:
            clean: 是否清理后编译
            verbose: 是否显示详细输出

        Returns:
            编译结果
        """
        print("🔨 编译驱动...")
        print(f"  - 清理编译: {'是' if clean else '否'}")
        print(f"  - 详细输出: {'是' if verbose else '否'}")

        result = await self.client.call_tool(
            "driver_compile",
            {
                "clean": clean,
                "verbose": verbose
            }
        )

        if result.get("success"):
            print(f"✅ 编译成功")
            if "build_output" in result:
                print("编译输出:")
                for line in result["build_output"].split("\n")[:10]:
                    print(f"  {line}")
        else:
            print(f"❌ 编译失败: {result.get('error')}")

        return result

    async def load_driver(
        self,
        module_name: str,
        parameters: Optional[Dict[str, str]] = None,
        check_logs: bool = True
    ) -> Dict[str, Any]:
        """
        加载驱动并检查日志.

        Args:
            module_name: 模块名（不含 .ko）
            parameters: 模块参数
            check_logs: 是否检查加载后的日志

        Returns:
            加载结果
        """
        print(f"📦 加载驱动: {module_name}")
        if parameters:
            print(f"  参数: {parameters}")

        # 加载驱动
        result = await self.client.call_tool(
            "driver_load",
            {
                "operation": "load",
                "module_name": module_name,
                "parameters": parameters or {}
            }
        )

        if result.get("success"):
            print(f"✅ 驱动加载成功")

            # 检查日志
            if check_logs:
                await asyncio.sleep(1)  # 等待日志生成
                print("\n📋 检查内核日志...")

                log_result = await self.client.call_tool(
                    "log_viewer",
                    {
                        "source": "dmesg",
                        "lines": 20,
                        "filter_pattern": module_name
                    }
                )

                logs = log_result.get("logs", [])
                if logs:
                    print("相关日志:")
                    for log in logs[:10]:
                        print(f"  {log}")

                    # 检查错误
                    errors = [log for log in logs if "error" in log.lower() or "fail" in log.lower()]
                    if errors:
                        print(f"\n⚠️  发现 {len(errors)} 个错误")
                        result["has_errors"] = True
                        result["errors"] = errors
                else:
                    print("  (无相关日志)")
        else:
            print(f"❌ 驱动加载失败: {result.get('error')}")

        return result

    async def unload_driver(self, module_name: str, force: bool = False) -> Dict[str, Any]:
        """
        卸载驱动.

        Args:
            module_name: 模块名
            force: 是否强制卸载

        Returns:
            卸载结果
        """
        print(f"🗑️  卸载驱动: {module_name}")
        if force:
            print("  (强制卸载)")

        result = await self.client.call_tool(
            "driver_load",
            {
                "operation": "unload",
                "module_name": module_name,
                "force": force
            }
        )

        if result.get("success"):
            print(f"✅ 驱动卸载成功")
        else:
            print(f"❌ 驱动卸载失败: {result.get('error')}")

        return result

    async def full_cycle(
        self,
        module_name: str,
        parameters: Optional[Dict[str, str]] = None,
        clean_build: bool = False
    ) -> Dict[str, Any]:
        """
        完整的编译-加载-测试流程.

        Args:
            module_name: 模块名
            parameters: 模块参数
            clean_build: 是否清理编译

        Returns:
            流程结果
        """
        print("\n" + "="*60)
        print(f"🚀 开始完整测试流程: {module_name}")
        print("="*60 + "\n")

        results = {}

        # 1. 卸载旧驱动（如果存在）
        print("步骤 1/4: 卸载旧驱动")
        await self.unload_driver(module_name, force=True)
        print()

        # 2. 编译驱动
        print("步骤 2/4: 编译驱动")
        compile_result = await self.compile_driver(clean=clean_build, verbose=False)
        results["compile"] = compile_result
        print()

        if not compile_result.get("success"):
            print("❌ 编译失败，终止流程")
            return results

        # 3. 加载驱动
        print("步骤 3/4: 加载驱动")
        load_result = await self.load_driver(
            module_name,
            parameters=parameters,
            check_logs=True
        )
        results["load"] = load_result
        print()

        if not load_result.get("success"):
            print("❌ 加载失败，终止流程")
            return results

        # 4. 检查网络接口
        print("步骤 4/4: 检查网络接口")
        try:
            network_result = await self.client.call_tool(
                "network_info",
                {"interface": "all", "detail_level": "detailed"}
            )
            results["network"] = network_result
            print("✅ 网络接口检查完成")
        except Exception as e:
            print(f"⚠️  网络接口检查失败: {e}")

        print("\n" + "="*60)
        print("✅ 完整流程执行完毕")
        print("="*60 + "\n")

        return results


# ============================================================================
# 使用示例
# ============================================================================

async def example_basic_usage():
    """示例 1: 基本使用."""
    print("\n" + "="*60)
    print("示例 1: 基本使用")
    print("="*60 + "\n")

    async with KaliDriverMCPClient(MCP_SERVER_PATH, CONFIG_FILE) as client:
        # 列出工具
        print("📋 可用工具:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")

        print("\n" + "-"*60 + "\n")

        # 获取内核信息
        print("🔍 获取内核信息:")
        kernel_info = await client.call_tool("kernel_info", {"detail_level": "basic"})
        print(f"  版本: {kernel_info.get('version', 'N/A')}")
        print(f"  架构: {kernel_info.get('architecture', 'N/A')}")

        print("\n" + "-"*60 + "\n")

        # 验证共享文件夹
        print("📁 验证共享文件夹:")
        sync_result = await client.call_tool("code_sync", {})
        print(f"  状态: {'✅ 就绪' if sync_result.get('ready') else '❌ 未就绪'}")
        print(f"  VM 路径: {sync_result.get('vm_path', 'N/A')}")


async def example_driver_debugging():
    """示例 2: 驱动调试."""
    print("\n" + "="*60)
    print("示例 2: 驱动调试")
    print("="*60 + "\n")

    async with KaliDriverMCPClient(MCP_SERVER_PATH, CONFIG_FILE) as client:
        debugger = DriverDebugger(client)

        # 检查环境
        env_result = await debugger.check_environment()

        if env_result["ready"]:
            # 执行完整流程
            await debugger.full_cycle(
                module_name="mydriver",
                parameters={"debug": "1"},
                clean_build=True
            )
        else:
            print("❌ 环境未就绪，跳过驱动测试")


async def example_batch_testing():
    """示例 3: 批量测试."""
    print("\n" + "="*60)
    print("示例 3: 批量测试不同参数")
    print("="*60 + "\n")

    test_cases = [
        {"debug": "0", "mode": "normal"},
        {"debug": "1", "mode": "normal"},
        {"debug": "1", "mode": "test"},
    ]

    async with KaliDriverMCPClient(MCP_SERVER_PATH, CONFIG_FILE) as client:
        debugger = DriverDebugger(client)

        results = []

        for i, params in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"测试用例 {i}/{len(test_cases)}: {params}")
            print(f"{'='*60}\n")

            result = await debugger.full_cycle(
                module_name="mydriver",
                parameters=params,
                clean_build=(i == 1)  # 只在第一次清理编译
            )

            results.append({
                "case": i,
                "params": params,
                "success": result.get("load", {}).get("success", False)
            })

            # 测试间隔
            if i < len(test_cases):
                print("\n⏸️  等待 3 秒...\n")
                await asyncio.sleep(3)

        # 输出汇总
        print(f"\n{'='*60}")
        print("📊 测试汇总")
        print(f"{'='*60}\n")

        passed = sum(1 for r in results if r["success"])
        print(f"✅ 通过: {passed}/{len(results)}")
        print(f"❌ 失败: {len(results) - passed}/{len(results)}\n")


async def example_network_monitoring():
    """示例 4: 网络监控和抓包."""
    print("\n" + "="*60)
    print("示例 4: 网络监控和抓包")
    print("="*60 + "\n")

    async with KaliDriverMCPClient(MCP_SERVER_PATH, CONFIG_FILE) as client:
        try:
            # 1. 启动监控模式
            print("📡 启动监控模式...")
            result = await client.call_tool(
                "network_monitor",
                {"operation": "start", "channel": 6}
            )

            if result.get("success"):
                print(f"✅ 监控模式已启动在频道 6")

                # 2. 捕获数据包
                print("\n📻 开始抓包 (30 秒)...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                capture_result = await client.call_tool(
                    "packet_capture",
                    {
                        "channel": 6,
                        "duration": 30,
                        "output_prefix": f"demo_{timestamp}"
                    }
                )

                if capture_result.get("success"):
                    print("✅ 抓包完成")
                    print(f"  文件: {capture_result.get('capture_file')}")

                    stats = capture_result.get("statistics", {})
                    if stats:
                        print(f"  统计:")
                        print(f"    - AP 数量: {stats.get('access_points', 0)}")
                        print(f"    - 客户端: {stats.get('clients', 0)}")
                else:
                    print(f"❌ 抓包失败: {capture_result.get('error')}")

            else:
                print(f"❌ 启动监控模式失败: {result.get('error')}")

        finally:
            # 3. 停止监控模式
            print("\n🛑 停止监控模式...")
            await client.call_tool(
                "network_monitor",
                {"operation": "stop"}
            )
            print("✅ 监控模式已停止")


# ============================================================================
# 主程序
# ============================================================================

async def main():
    """主函数."""
    print("\n" + "="*60)
    print("Kali Driver MCP 客户端示例")
    print("="*60)

    # 选择要运行的示例
    examples = {
        "1": ("基本使用", example_basic_usage),
        "2": ("驱动调试", example_driver_debugging),
        "3": ("批量测试", example_batch_testing),
        "4": ("网络监控", example_network_monitoring),
    }

    print("\n请选择要运行的示例:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  0. 运行所有示例")

    choice = input("\n请输入选项 (0-4): ").strip()

    print()

    try:
        if choice == "0":
            # 运行所有示例
            for name, func in examples.values():
                await func()
        elif choice in examples:
            # 运行选定的示例
            _, func = examples[choice]
            await func()
        else:
            print("❌ 无效选项")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("示例执行完毕")
    print("="*60 + "\n")


if __name__ == "__main__":
    # 检查配置
    import os

    if not os.path.exists(MCP_SERVER_PATH):
        print(f"❌ 错误: MCP 服务器路径不存在: {MCP_SERVER_PATH}")
        print("请修改脚本开头的 MCP_SERVER_PATH 变量")
        exit(1)

    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 错误: 配置文件不存在: {CONFIG_FILE}")
        print("请确保 config.yaml 已正确配置")
        exit(1)

    # 运行主程序
    asyncio.run(main())
