param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")

class R2eHookAfterMCPExecutionInputBody {
  [string]$session_id
  [string]$tool_name
  [hashtable]$tool_input
  [string]$result_json
  [long]$duration
  [hashtable]$others

  R2eHookAfterMCPExecutionInputBody() {
    $this.duration = 0
  }

  [string] ToJsonString() {
    $h = @{
      tool_name   = $this.tool_name
      tool_input  = $this.tool_input
      result_json = $this.result_json
      duration    = $this.duration
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Set-AfterMcpHookFallbackJsonLongField {
  [CmdletBinding()]
  param(
    [Parameter(Mandatory = $true, Position = 0)]
    $Target,

    [Parameter(Mandatory = $true, Position = 1)]
    [ValidateNotNullOrEmpty()]
    [string]$MemberName,

    [Parameter(Mandatory = $true, Position = 2)]
    [AllowEmptyString()]
    [string]$Text,

    [Parameter(Mandatory = $false)]
    [ValidateNotNullOrEmpty()]
    [string]$JsonFieldName
  )
  $key = if ($PSBoundParameters.ContainsKey('JsonFieldName')) { $JsonFieldName } else { $MemberName }
  $pattern = '"' + [regex]::Escape($key) + '"\s*:\s*(-?\d+)'
  $cap = Get-HookFallbackRegexCapture -Text $Text -Pattern $pattern
  if ($null -eq $cap) { return }

  $Target.$MemberName = [long]$cap
}

function Get-HookInputBody {
  $head, $bodyStr = Get-HookInputHeadAndBody

  if ([string]::IsNullOrWhiteSpace($bodyStr)) {
    return $head, ([R2eHookAfterMCPExecutionInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookAfterMCPExecutionInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst tool_name $bodyStr
    Set-HookFallbackJsonQuotedField $inst result_json $bodyStr
    Set-AfterMcpHookFallbackJsonLongField $inst duration $bodyStr
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookAfterMCPExecutionInputBody]::new()

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
    if ($obj.PSObject.Properties["result_json"]) {
      $v = $obj.result_json
      if ($null -ne $v) {
        if ($v -is [string]) {
          $inst.result_json = $v
        } elseif ($v -is [System.Management.Automation.PSCustomObject]) {
          $inst.result_json = ConvertTo-R2eHookEventLogJson -InputObject $v -Depth 20
        } else {
          $inst.result_json = [string]$v
        }
      }
      $obj.PSObject.Properties.Remove("result_json")
    }
    if ($obj.PSObject.Properties["duration"]) {
      $v = $obj.duration
      if ($null -ne $v) {
        $inst.duration = [long]$v
      }
      $obj.PSObject.Properties.Remove("duration")
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
    $inst = [R2eHookAfterMCPExecutionInputBody]::new()
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


# Hook: afterMCPExecution
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





