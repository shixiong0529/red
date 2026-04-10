# chat.slow.best HTTPS 自动续期方案

当前状态：

- `chat.slow.best` 的线上证书已经可用。
- 它是通过 `certbot --manual --preferred-challenges dns` 签发的。
- 手动签发的证书不会自动续期。

如果要真正解决续期问题，需要把当前方案切换成基于 DNS API 的自动验证流程。

## 推荐方案

使用 `acme.sh` 配合阿里云 DNS API（`dns_ali`）。

推荐原因：

- 支持自动 DNS 验证
- 可以绕开之前 HTTP 验证返回 `403` 的问题
- 不需要每次续证时手动添加 TXT 记录

## 前置准备

在阿里云创建一个 RAM 用户，并授予它管理当前域名 DNS 记录的权限。

权限建议：

- 只授予管理阿里云 DNS 所需的最小权限
- 不要使用阿里云主账号的 AccessKey

你需要准备：

- `Ali_Key`
- `Ali_Secret`

阿里云官方通常建议通过 RAM 用户 + AccessKey 的方式调用 API。

## 1. 安装 acme.sh

```bash
curl https://get.acme.sh | sh
source ~/.bashrc
```

作用：为当前用户安装 `acme.sh`，并注册它自带的定时续期任务。

如果 `source ~/.bashrc` 不生效，可以退出终端后重新登录。

## 2. 配置阿里云 DNS API 凭据

```bash
export Ali_Key="REPLACE_WITH_YOUR_ACCESS_KEY_ID"
export Ali_Secret="REPLACE_WITH_YOUR_ACCESS_KEY_SECRET"
```

作用：让 `acme.sh` 可以通过阿里云 DNS API 自动创建和删除 TXT 验证记录。

注意：

- `acme.sh` 第一次成功签发后，会把这些配置保存到自己的账户配置中
- 后续不一定需要每次都重新 export
- 但请务必把 AccessKey 保存到安全的密码管理工具中

## 3. 自动签发新的 RSA 证书

```bash
~/.acme.sh/acme.sh --set-default-ca --server letsencrypt
~/.acme.sh/acme.sh --issue --dns dns_ali -d chat.slow.best --keylength 2048
```

作用：通过阿里云 DNS API 自动签发一张新的 `chat.slow.best` RSA 证书。

## 4. 把证书安装到 nginx 当前使用的路径

```bash
mkdir -p /etc/letsencrypt/live/chat.slow.best
~/.acme.sh/acme.sh --install-cert -d chat.slow.best \
  --key-file /etc/letsencrypt/live/chat.slow.best/privkey.pem \
  --fullchain-file /etc/letsencrypt/live/chat.slow.best/fullchain.pem \
  --reloadcmd "systemctl reload nginx"
```

作用：把续签后的证书复制到 nginx 当前正在使用的证书路径，并在续签完成后自动 reload nginx。

## 5. 测试续期流程

```bash
~/.acme.sh/acme.sh --renew -d chat.slow.best --force
```

作用：在真正依赖自动续期前，手动测试整条续签链路是否工作正常。

然后执行：

```bash
systemctl status nginx --no-pager
curl -Iv https://chat.slow.best
```

作用：检查 nginx 是否正常，并确认服务器对外提供的证书已经续签成功。

## 6. certbot 可以保留吗

可以保留 `certbot`，但一旦切换到 `acme.sh` 后，真正生效的续期流程应当是：

- 签发：`acme.sh --issue --dns dns_ali`
- 安装：`acme.sh --install-cert`
- 续期：由 `acme.sh` 自带的定时任务负责

## 7. 回滚方案

如果自动签发失败：

- 当前已经签发好的证书仍然会继续使用，直到到期
- nginx 也会继续提供当前已安装的证书

这意味着你可以在证书到期前安全地测试自动续期方案，而不会立刻影响线上站点。
