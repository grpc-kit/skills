import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("sync_openapiv2_methods.py")


class SyncOpenAPIv2MethodsTest(unittest.TestCase):
    def load_module(self):
        self.assertTrue(SCRIPT_PATH.exists(), f"missing sync utility: {SCRIPT_PATH}")
        spec = importlib.util.spec_from_file_location("sync_openapiv2_methods", SCRIPT_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_sync_preserves_existing_block_and_generates_missing_method(self):
        module = self.load_module()
        gateway_text = """type: google.api.Service
config_version: 3
http:
  rules:
  - selector: grpc_kit.api.known.admin.v1.KnownAdmin.CreateAuthLogin
    post: \"/builtin/admin/api/v1/auth/login\"
    body: \"*\"
  - selector: grpc_kit.api.known.admin.v1.KnownAdmin.ListServices
    get: \"/builtin/admin/api/v1/services\"
"""
        openapi_text = """openapiOptions:
  file:
    - file: \"known/admin/v1/admin.proto\"
      option:
        swagger: \"2.0\"
  method:
    - method: grpc_kit.api.known.admin.v1.KnownAdmin.CreateAuthLogin
      option:
        tags:
          - \"认证鉴权\"
        summary: \"登录认证\"
        description: \"接口格式：/builtin/admin/api/v1/auth/login。\"
        responses:
          \"200\":
            examples:
              \"application/json\": '{\"access_token\":\"token\"}'
"""

        synced = module.sync_openapi_methods(gateway_text, openapi_text)

        blocks = module.parse_method_blocks(synced)
        methods = [block["method"] for block in blocks]
        self.assertEqual(
            methods,
            [
                "grpc_kit.api.known.admin.v1.KnownAdmin.CreateAuthLogin",
                "grpc_kit.api.known.admin.v1.KnownAdmin.ListServices",
            ],
        )

        self.assertIn('summary: "登录认证"', synced)
        self.assertIn('description: "接口格式：/builtin/admin/api/v1/auth/login。"', synced)
        self.assertIn('method: grpc_kit.api.known.admin.v1.KnownAdmin.ListServices', synced)
        self.assertIn('description: "接口格式：GET /builtin/admin/api/v1/services。前置条件与业务约束待补充。"', synced)
        self.assertIn('"application/json": "{}"', synced)

    def test_sync_keeps_existing_extra_method_blocks_by_default(self):
        module = self.load_module()
        gateway_text = """type: google.api.Service
config_version: 3
http:
  rules:
  - selector: svc.Known.ListServices
    get: \"/builtin/admin/api/v1/services\"
"""
        openapi_text = """openapiOptions:
  file:
    - file: \"known/admin/v1/admin.proto\"
      option:
        swagger: \"2.0\"
  method:
    - method: svc.Known.ListServices
      option:
        tags:
          - \"服务字典管理\"
        summary: \"服务列表\"
        description: \"接口格式：/builtin/admin/api/v1/services。\"
        responses:
          \"200\":
            examples:
              \"application/json\": '{}'
    - method: svc.Known.LegacyOnly
      option:
        tags:
          - \"兼容接口\"
        summary: \"旧接口\"
        description: \"接口格式：/legacy。\"
        responses:
          \"200\":
            examples:
              \"application/json\": '{}'
"""

        synced = module.sync_openapi_methods(gateway_text, openapi_text)

        self.assertIn("svc.Known.LegacyOnly", synced)
        self.assertLess(synced.index("svc.Known.ListServices"), synced.index("svc.Known.LegacyOnly"))

    def test_cli_updates_file_in_place(self):
        module = self.load_module()
        gateway_text = """type: google.api.Service
config_version: 3
http:
  rules:
  - selector: grpc_kit.api.known.admin.v1.KnownAdmin.ListServices
    get: \"/builtin/admin/api/v1/services\"
"""
        openapi_text = """openapiOptions:
  file:
    - file: \"known/admin/v1/admin.proto\"
      option:
        swagger: \"2.0\"
  method:
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            service_dir = Path(tmp_dir)
            gateway_path = service_dir / "admin.gateway.yaml"
            openapi_path = service_dir / "admin.openapiv2.yaml"
            gateway_path.write_text(gateway_text, encoding="utf-8")
            openapi_path.write_text(openapi_text, encoding="utf-8")

            exit_code = module.main([
                "--gateway-file",
                str(gateway_path),
                "--openapi-file",
                str(openapi_path),
            ])

            self.assertEqual(exit_code, 0)
            synced = openapi_path.read_text(encoding="utf-8")
            self.assertIn("KnownAdmin.ListServices", synced)
            self.assertIn('summary: "TODO: 补充 ListServices 摘要"', synced)

    def test_cli_returns_2_when_input_file_is_missing(self):
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp_dir:
            service_dir = Path(tmp_dir)
            gateway_path = service_dir / "missing.gateway.yaml"
            openapi_path = service_dir / "admin.openapiv2.yaml"
            openapi_path.write_text("openapiOptions:\n  method:\n", encoding="utf-8")

            exit_code = module.main([
                "--gateway-file",
                str(gateway_path),
                "--openapi-file",
                str(openapi_path),
            ])

            self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()