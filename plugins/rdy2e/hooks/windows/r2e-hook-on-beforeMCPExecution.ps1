param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")

class R2eHookBeforeMCPExecutionInputBody {
  [string]$session_id
  [string]$tool_name
  [hashtable]$tool_input
  [string]$url
  [string]$command
  [hashtable]$others

  [string] ToJsonString() {
    $h = @{
      tool_name  = $this.tool_name
      tool_input = $this.tool_input
      url        = $this.url
      command    = $this.command
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
    return $head, ([R2eHookBeforeMCPExecutionInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookBeforeMCPExecutionInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst tool_name $bodyStr
    Set-HookFallbackJsonQuotedField $inst url $bodyStr
    Set-HookFallbackJsonQuotedField $inst command $bodyStr -Convert { param($cap) '...' }
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookBeforeMCPExecutionInputBody]::new()

    if ($obj.PSObject.Properties["session_id"]) {
      $v = $obj.session_id
      if ($null -ne $v) {
        $inst.session_id = Get-PrettyUuid -Id ([string]$v)
      }
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["tool_name"]) {
      $inst.tool_name = [string]$obj.tool_name
      $obj.PSObject.Properties.Remove("tool_name")
    }
    if ($obj.PSObject.Properties["tool_input"]) {
      $inst.tool_input = ConvertFrom-R2eHookMcpToolInputForLog -ToolInput $obj.tool_input
      $obj.PSObject.Properties.Remove("tool_input")
    }
    if ($obj.PSObject.Properties["url"]) {
      $inst.url = [string]$obj.url
      $obj.PSObject.Properties.Remove("url")
    }
    if ($obj.PSObject.Properties["command"]) {
      if ($null -ne $obj.command) {
        $inst.command = '...'
      }
      $obj.PSObject.Properties.Remove("command")
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
    $inst = [R2eHookBeforeMCPExecutionInputBody]::new()
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
    permission = "allow"
    user_message = "ok"
  }
  return ($payload | ConvertTo-Json -Compress)
}


# Hook: beforeMCPExecution
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





