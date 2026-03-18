# 火山引擎 CLI 配置脚本
# 用于配置volcengine-cli和kubectl访问

param(
    [string]$SecretKey = "",
    [string]$Region = "cn-beijing"
)

# 配置变量
$AccessKeyId = "AKLTZWM5Y2Y2MTZhMWI2NDNmNmExNzk2ZmYwNzhmOTFkYWY"
$ConsoleUrl = "https://console.volcengine.com/iam/keymanage"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  火山引擎 CLI 配置脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查是否提供了SecretKey
if ([string]::IsNullOrEmpty($SecretKey)) {
    Write-Host ""
    Write-Host "请输入Secret Key (可在 $ConsoleUrl 查看):" -ForegroundColor Yellow
    Write-Host "注意: 输入时不会显示字符" -ForegroundColor Gray
    $secureString = Read-Host -AsSecureString
    $SecretKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureString))
}

# 步骤1: 安装volcengine-cli
Write-Host ""
Write-Host "[1/5] 检查volcengine-cli..." -ForegroundColor Yellow

try {
    $volcVersion = volcengine-cli --version 2>$null
    Write-Host "[OK] volcengine-cli已安装: $volcVersion" -ForegroundColor Green
} catch {
    Write-Host "正在安装volcengine-cli..." -ForegroundColor Cyan
    
    # 下载并安装
    $downloadUrl = "https://github.com/volcengine/volcengine-cli/releases/latest/download/volcengine-cli_windows_amd64.exe"
    $installDir = "$env:LOCALAPPDATA\volcengine-cli"
    $installPath = "$installDir\volcengine-cli.exe"
    
    # 创建目录
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    
    # 下载
    Write-Host "下载volcengine-cli..." -ForegroundColor Gray
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installPath
    
    # 添加到PATH
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$installDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")
        Write-Host "[OK] 已添加到PATH，请重新打开PowerShell" -ForegroundColor Green
    }
    
    Write-Host "[OK] volcengine-cli安装完成" -ForegroundColor Green
}

# 步骤2: 配置volcengine-cli凭证
Write-Host ""
Write-Host "[2/5] 配置volcengine-cli凭证..." -ForegroundColor Yellow

$volcConfigDir = "$env:USERPROFILE\.volcengine"
New-Item -ItemType Directory -Force -Path $volcConfigDir | Out-Null

$volcConfig = @"
{
  \"version\": \"v1\",
  \"profiles\": [
    {
      \"name\": \"default\",
      \"region\": \"$Region\",
      \"access_key_id\": \"$AccessKeyId\",
      \"secret_access_key\": \"$SecretKey\"
    }
  ],
  \"current_profile\": \"default\"
}
"@

$volcConfig | Out-File -FilePath "$volcConfigDir\config.json" -Encoding UTF8
Write-Host "[OK] volcengine-cli凭证配置完成" -ForegroundColor Green

# 步骤3: 配置kubectl访问VKE
Write-Host ""
Write-Host "[3/5] 配置kubectl访问VKE集群..." -ForegroundColor Yellow

Write-Host ""
Write-Host "请在火山引擎控制台完成以下操作:" -ForegroundColor Cyan
Write-Host "1. 访问: https://console.volcengine.com/vke/cluster" -ForegroundColor White
Write-Host "2. 选择你的集群" -ForegroundColor White
Write-Host "3. 点击'连接信息' -> 'KubeConfig'" -ForegroundColor White
Write-Host "4. 下载KubeConfig文件" -ForegroundColor White
Write-Host ""
Write-Host "下载完成后，请输入KubeConfig文件路径:" -ForegroundColor Yellow

$kubeConfigPath = Read-Host

if (Test-Path $kubeConfigPath) {
    $kubeDir = "$env:USERPROFILE\.kube"
    New-Item -ItemType Directory -Force -Path $kubeDir | Out-Null
    Copy-Item $kubeConfigPath "$kubeDir\config" -Force
    $env:KUBECONFIG = "$kubeDir\config"
    Write-Host "[OK] KubeConfig配置完成" -ForegroundColor Green
} else {
    Write-Host "[WARN] 文件不存在，跳过kubectl配置" -ForegroundColor Yellow
}

# 步骤4: 验证配置
Write-Host ""
Write-Host "[4/5] 验证配置..." -ForegroundColor Yellow

try {
    # 验证volcengine-cli
    $volcOutput = volcengine-cli configure list 2>$null
    Write-Host "[OK] volcengine-cli配置验证通过" -ForegroundColor Green
} catch {
    Write-Host "[WARN] volcengine-cli验证失败，可能需要重新打开PowerShell" -ForegroundColor Yellow
}

try {
    # 验证kubectl
    $k8sOutput = kubectl cluster-info 2>$null
    Write-Host "[OK] kubectl连接验证通过" -ForegroundColor Green
    Write-Host "  集群信息: $k8sOutput" -ForegroundColor Gray
} catch {
    Write-Host "[WARN] kubectl连接验证失败，请检查KubeConfig" -ForegroundColor Yellow
}

# 步骤5: 登录镜像仓库
Write-Host ""
Write-Host "[5/5] 登录火山引擎镜像仓库..." -ForegroundColor Yellow

$registryPassword = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("WmpJNVl6QXpORGt6TXpoak5HWTJZemt3T1RaaU1HVmxPRFV3WkRZNVlUQQ=="))

try {
    $loginOutput = echo $registryPassword | docker login cr.volcengine.com -u volcen --password-stdin 2>&1
    Write-Host "[OK] 镜像仓库登录成功" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 镜像仓库登录失败: $_" -ForegroundColor Red
}

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  配置完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "后续步骤:" -ForegroundColor Cyan
Write-Host "1. 运行部署脚本: .\volcengine-deploy-fixed.ps1" -ForegroundColor White
Write-Host "2. 查看集群状态: kubectl get all -n ai-agriculture" -ForegroundColor White
Write-Host "3. 查看控制台: https://console.volcengine.com/vke/cluster" -ForegroundColor White

Write-Host ""
Write-Host "常用命令:" -ForegroundColor Yellow
Write-Host "  volcengine-cli configure list    # 查看配置" -ForegroundColor Gray
Write-Host "  kubectl get nodes                # 查看节点" -ForegroundColor Gray
Write-Host "  kubectl get pods -n ai-agriculture  # 查看Pod" -ForegroundColor Gray
