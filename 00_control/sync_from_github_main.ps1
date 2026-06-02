param(
    [string]$Repo = "cocyuhao/park-commercial-site-selection-simulation",
    [string]$Branch = "main",
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Invoke-GitFetch {
    param(
        [string]$RemoteBranch,
        [string]$AuthToken = ""
    )

    $args = @(
        "-c", "http.lowSpeedLimit=0",
        "-c", "http.lowSpeedTime=999"
    )
    if ($AuthToken) {
        $args += @("-c", "http.extraheader=AUTHORIZATION: bearer $AuthToken")
    }
    $args += @("fetch", "origin", $RemoteBranch)

    & git @args
    return $LASTEXITCODE
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

if (-not (Test-Path ".git")) {
    throw "Current project root has no .git directory: $Root"
}

Write-Step "Check remote latest commit"
$latest = gh api -X GET "repos/$Repo/commits/$Branch" --jq "{sha: .sha, message: .commit.message, date: .commit.committer.date}"
Write-Host $latest

Write-Step "Fetch origin/$Branch"
$fetchExit = Invoke-GitFetch -RemoteBranch $Branch

if ($fetchExit -ne 0) {
    Write-Step "Plain git fetch failed; retry with gh auth token"
    $token = (& gh auth token).Trim()
    if (-not $token) {
        throw "gh auth token is empty; run gh auth login first."
    }
    $fetchExit = Invoke-GitFetch -RemoteBranch $Branch -AuthToken $token
}

if ($fetchExit -eq 0) {
    Write-Step "Reset local working tree to origin/$Branch"
    & git reset --hard "origin/$Branch"
    if ($LASTEXITCODE -ne 0) {
        throw "git reset failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Step "Fetch still failed; mirror GitHub codeload ZIP while preserving .git and .env"
    $token = (& gh auth token).Trim()
    $zip = Join-Path $env:TEMP "park-commercial-site-selection-$Branch.zip"
    $extract = Join-Path $env:TEMP "park-commercial-site-selection-$Branch"
    if (Test-Path $zip) {
        Remove-Item -LiteralPath $zip -Force
    }
    if (Test-Path $extract) {
        Remove-Item -LiteralPath $extract -Recurse -Force
    }

    curl.exe -L --fail --connect-timeout 20 --max-time 240 `
        -H "Authorization: Bearer $token" `
        -H "User-Agent: Codex" `
        -o $zip `
        "https://api.github.com/repos/$Repo/zipball/$Branch"

    $headerStream = [System.IO.File]::OpenRead($zip)
    try {
        $header = New-Object byte[] 4
        [void]$headerStream.Read($header, 0, 4)
    } finally {
        $headerStream.Close()
    }
    $headerText = ($header | ForEach-Object { $_.ToString("X2") }) -join " "
    if ($headerText -ne "50 4B 03 04") {
        throw "Downloaded file is not a ZIP archive. Header: $headerText"
    }

    New-Item -ItemType Directory -Path $extract | Out-Null
    Expand-Archive -LiteralPath $zip -DestinationPath $extract -Force
    $src = (Get-ChildItem -LiteralPath $extract | Select-Object -First 1).FullName
    if (-not $src) {
        throw "Extracted source folder not found."
    }

    robocopy $src $Root /MIR /XD .git /XF .env /R:2 /W:2 /NP
    $roboExit = $LASTEXITCODE
    Write-Host "ROBOCOPY_EXIT=$roboExit"
    if ($roboExit -ge 8) {
        throw "robocopy failed with exit code $roboExit"
    }

    Write-Warning "ZIP mirror completed, but Git metadata may still need a successful fetch."
}

if (-not $SkipDependencyInstall) {
    Write-Step "Install or update Python dependencies from requirements.txt"
    & py -3.12 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed with exit code $LASTEXITCODE"
    }
}

Write-Step "Verify synced state"
$head = (& git rev-parse HEAD).Trim()
$status = (& git status --short)
Write-Host "HEAD=$head"
if ($status) {
    Write-Host $status
} else {
    Write-Host "working_tree=clean"
}

Write-Step "Run minimum project checks"
& node --check "90_p6_expert_dashboard\static\app.js"
if ($LASTEXITCODE -ne 0) {
    throw "node --check failed with exit code $LASTEXITCODE"
}

& py -3.12 -m py_compile `
    "90_p6_expert_dashboard\app.py" `
    "60_model\db\store.py" `
    "60_model\simulation\engine.py" `
    "60_model\simulation\validators.py"
if ($LASTEXITCODE -ne 0) {
    throw "py_compile failed with exit code $LASTEXITCODE"
}

& py -3.12 "30_extraction\scripts\verify_project_implementation.py"
if ($LASTEXITCODE -ne 0) {
    throw "verify_project_implementation.py failed with exit code $LASTEXITCODE"
}

Write-Step "Done"
