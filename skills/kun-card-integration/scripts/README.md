# 联调脚本

帮助商户在沙箱**几分钟内**发出已签名请求。

```bash
pip install -r requirements.txt
python kun_client.py gen-key --out-dir ./keys
# 将 merchant_public.pem 配到开放平台后：
python kun_client.py call --env sandbox \
  --app-key YOUR_APP_KEY \
  --customer-no YOUR_CUSTOMER_NO \
  --private-key ./keys/merchant_private.pem \
  --path /rest/v2.0/api/common/cardBins \
  --body '{"requestNo":"r1","secretKey":"YOUR_SECRET_KEY","ip":"127.0.0.1"}'
```

| 命令 | 作用 |
|------|------|
| `gen-key` | 生成本地 RSA2048 密钥对 |
| `sign-string` | 打印待签字符串，便于对签 |
| `call` | 签名并 POST；`--dry-run` 不发网 |
| `lookup_mapping.py <旧path或id>` | 旧 VCC → 新 API 对照 |
| `lookup_mapping.py --list-pending` | 列出 pending_add / split / new_only |

字段与黄金路径见 `../references/产品能力/最小跑通.md`；迁移见 `../references/迁移/`。
