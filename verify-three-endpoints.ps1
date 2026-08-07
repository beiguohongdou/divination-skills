# 三端 junction 联调抽检（推荐用 Python 版，避免 PowerShell 中文编码问题）：
#   py -3 skills/divination-skills/verify-three-endpoints.py

$ErrorActionPreference = "Stop"
$AnchorDate = "2026-07-04"
$AnchorTime = "06:00"
$Anchor = "$AnchorDate $AnchorTime"

$Expected = @{
    本卦   = "地雷复"
    年数   = 7
    变卦   = "山雷颐"
    体用生克 = "体克用"
}

$Endpoints = @(
    @{ Name = "Cursor (.agents)"; Root = "E:\HanakoWorkSpace\.agents\skills\yijing-divination" }
    @{ Name = "Claude"; Root = "$env:USERPROFILE\.claude\skills\yijing-divination" }
    @{ Name = "Hanako"; Root = "$env:USERPROFILE\.hanako\skills\yijing-divination" }
)

$StandardPrompt = @"
请用梅花易数时间起卦：公历 $Anchor，问「今日运势如何」。
要求：必须先运行 meihua_time.py（禁止心算）；解读前先给 6 行摘要。
"@

Write-Host "=== 三端 junction 脚本联调（锚点: $Anchor）===" -ForegroundColor Cyan
Write-Host ""
Write-Host "【标准 UI 抽检 prompt】（复制到 Cursor / Claude / Hanako 各测一遍）" -ForegroundColor Yellow
Write-Host $StandardPrompt
Write-Host ""

$allOk = $true
$rows = @()

foreach ($ep in $Endpoints) {
    $scripts = Join-Path $ep.Root "scripts"
    $meihua = Join-Path $scripts "meihua_time.py"
    if (-not (Test-Path $meihua)) {
        $rows += [PSCustomObject]@{
            端点 = $ep.Name
            状态 = "FAIL"
            本卦 = "-"
            年数 = "-"
            变卦 = "-"
            体用 = "-"
            说明 = "未找到 $meihua"
        }
        $allOk = $false
        continue
    }

    Push-Location $scripts
    try {
        $jsonText = & py -3 meihua_time.py $AnchorDate $AnchorTime --json 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            throw "exit $LASTEXITCODE : $jsonText"
        }
        $data = $jsonText | ConvertFrom-Json
        $ben = $data.本卦.name
        $nian = [int]$data.取数.年数.值
        $bian = $data.变卦.name
        $ty = $data.体用.生克

        $ok = ($ben -eq $Expected.本卦) -and ($nian -eq $Expected.年数) -and ($bian -eq $Expected.变卦) -and ($ty -eq $Expected.体用生克)
        if (-not $ok) { $allOk = $false }

        $rows += [PSCustomObject]@{
            端点 = $ep.Name
            状态 = $(if ($ok) { "PASS" } else { "FAIL" })
            本卦 = $ben
            年数 = $nian
            变卦 = $bian
            体用 = $ty
            说明 = $(if ($ok) { "与锚点一致" } else { "与期望不符" })
        }
    }
    catch {
        $allOk = $false
        $rows += [PSCustomObject]@{
            端点 = $ep.Name
            状态 = "FAIL"
            本卦 = "-"
            年数 = "-"
            变卦 = "-"
            体用 = "-"
            说明 = $_.Exception.Message
        }
    }
    finally {
        Pop-Location
    }
}

$rows | Format-Table -AutoSize

Write-Host "期望: 本卦=$($Expected.本卦) 年数=$($Expected.年数) 变卦=$($Expected.变卦) 体用=$($Expected.体用生克)"
Write-Host ""

# 顺带验证三式脚本可从 yijing junction 相对路径调用
$yijingScripts = Join-Path $Endpoints[0].Root "scripts"
Push-Location $yijingScripts
try {
    $daliuren = Join-Path (Split-Path (Split-Path $yijingScripts -Parent) -Parent) "daliuren-divination\scripts\daliuren.py"
    $qimen = Join-Path (Split-Path (Split-Path $yijingScripts -Parent) -Parent) "qimen-dunjia\scripts\qimen.py"
    Write-Host "=== 跨 skill 路径抽检（自 yijing scripts 目录）===" -ForegroundColor Cyan
    if (Test-Path $daliuren) {
        & py -3 $daliuren --json $AnchorDate $AnchorTime | Select-Object -First 1 | ForEach-Object { Write-Host "daliuren: OK ($_...)" }
    } else { Write-Host "daliuren: FAIL 未找到 $daliuren" -ForegroundColor Red; $allOk = $false }
    if (Test-Path $qimen) {
        & py -3 $qimen --json $AnchorDate $AnchorTime | Select-Object -First 1 | ForEach-Object { Write-Host "qimen: OK ($_...)" }
    } else { Write-Host "qimen: FAIL 未找到 $qimen" -ForegroundColor Red; $allOk = $false }
}
finally {
    Pop-Location
}

Write-Host ""
if ($allOk) {
    Write-Host "总体: PASS（脚本层三端一致）" -ForegroundColor Green
    Write-Host "UI 层请在三端各粘贴上方标准 prompt，人工确认 Agent 是否跑脚本且卦象一致。" -ForegroundColor Yellow
    exit 0
}
else {
    Write-Host "总体: FAIL" -ForegroundColor Red
    exit 1
}
