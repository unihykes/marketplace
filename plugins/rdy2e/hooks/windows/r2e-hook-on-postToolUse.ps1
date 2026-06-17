<#
Hook: postToolUse
在工具调用完成后触发。
#>

param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")


class R2eHookPostToolUseInputBody {
  [string]$session_id
  [string]$tool_name
  [string]$tool_use_id
  [string]$cwd
  [double]$duration
  [string]$model
  [hashtable]$tool_input
  [hashtable]$tool_output
  [hashtable]$others

  R2eHookPostToolUseInputBody() {
    $this.tool_input = @{}
    $this.tool_output = @{}
  }

  [string] ToJsonString() {
    $h = @{
      tool_name    = $this.tool_name
      tool_use_id  = $this.tool_use_id
      cwd          = $this.cwd
      duration     = $this.duration
      model        = $this.model
      tool_input   = $this.tool_input
      tool_output  = $this.tool_output
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Get-HookInputBody {
  $head, $bodyStr = Get-HookInputHeadAndBody

  if ([string]::IsNullOrWhiteSpace($bodyStr)) {
    return $head, ([R2eHookPostToolUseInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookPostToolUseInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst tool_name $bodyStr
    Set-HookFallbackJsonQuotedField $inst tool_use_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst cwd $bodyStr
    Set-HookFallbackJsonQuotedField $inst model $bodyStr
    $durCap = Get-HookFallbackRegexCapture -Text $bodyStr -Pattern '"duration"\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)'
    if ($null -ne $durCap) {
      try {
        $inst.duration = [double]::Parse($durCap, [System.Globalization.CultureInfo]::InvariantCulture)
      } catch { }
    }
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookPostToolUseInputBody]::new()
    if ($obj.PSObject.Properties["session_id"]) {
      $inst.session_id = Get-PrettyUuid -Id ([string]$obj.session_id)
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["tool_name"]) {
      $inst.tool_name = [string]$obj.tool_name
      $obj.PSObject.Properties.Remove("tool_name")
    }
    if ($obj.PSObject.Properties["tool_use_id"]) {
      $inst.tool_use_id = Get-PrettyUuid -Id ([string]$obj.tool_use_id)
      $obj.PSObject.Properties.Remove("tool_use_id")
    }
    if ($obj.PSObject.Properties["cwd"]) {
      $inst.cwd = [string]$obj.cwd
      $obj.PSObject.Properties.Remove("cwd")
    }
    if ($obj.PSObject.Properties["duration"]) {
      try {
        $inst.duration = [double]$obj.duration
      }
      catch { }
      $obj.PSObject.Properties.Remove("duration")
    }
    if ($obj.PSObject.Properties["model"]) {
      $inst.model = [string]$obj.model
      $obj.PSObject.Properties.Remove("model")
    }
    if ($obj.PSObject.Properties["tool_input"]) {
      $inst.tool_input = ConvertTo-R2eHookMaskedObjectHashtable -InputObject $obj.tool_input
      $obj.PSObject.Properties.Remove("tool_input")
    }
    if ($obj.PSObject.Properties["tool_output"]) {
      $inst.tool_output = ConvertFrom-R2eHookToolOutputForLog -ToolOutput $obj.tool_output
      Apply-R2eHookPostToolUseOutputFilePathDedup -ToolOutputHt $inst.tool_output -ToolInputHt $inst.tool_input
      $obj.PSObject.Properties.Remove("tool_output")
    }
    foreach ($prop in $obj.PSObject.Properties) {
      if ($null -eq $inst.others) {
        $inst.others = @{}
      }
      $inst.others[$prop.Name] = $prop.Value
    }
    return $head, $inst
  }
  catch {
    $inst = [R2eHookPostToolUseInputBody]::new()
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }
}

function Build-HookResponse {
  <#
    生成传给 Cursor hook 的应答 JSON 字符串（不写 stdout）；调用方对返回值自行 Write-Output。
    默认：permission 放行。
  #>
  $payload = @{
    permission   = "allow"
    user_message = "ok"
  }
  return ($payload | ConvertTo-Json -Compress)
}

Set-HookOutputUtf8
$head, $body = Get-HookInputBody
Add-Content -Encoding utf8 -Path (Get-HookProjectLogPath) -Value (
  "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')]" +
    "[$($head.WorkspaceName)]" +
    "[$(Get-PrettyUuid -Id $head.ConversationId)]" +
    "[$(Get-PrettyUuid -Id $head.GenerationId)]" +
    "[$($head.ModelName)]" +
    "[$($head.HookEventName)]" +
    " " +
    $( $body.ToJsonString() )
)
$response = Build-HookResponse
Write-Output $response
exit 0


