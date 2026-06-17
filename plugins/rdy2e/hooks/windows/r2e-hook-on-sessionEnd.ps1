param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")


class R2eHookSessionEndInputBody {
  [string]$session_id
  [string]$reason
  [long]$duration_ms
  [bool]$is_background_agent
  [string]$final_status
  [string]$error_message
  [hashtable]$others

  R2eHookSessionEndInputBody() {
    $this.duration_ms = 0
    $this.is_background_agent = $false
  }

  [string] ToJsonString() {
    $h = @{
      reason                = $this.reason
      duration_ms           = $this.duration_ms
      is_background_agent   = $this.is_background_agent
      final_status          = $this.final_status
      error_message         = $this.error_message
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Set-SessionEndHookFallbackJsonLongField {
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
    return $head, ([R2eHookSessionEndInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookSessionEndInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst reason $bodyStr
    Set-SessionEndHookFallbackJsonLongField $inst duration_ms $bodyStr
    Set-HookFallbackJsonBoolField $inst is_background_agent $bodyStr
    Set-HookFallbackJsonQuotedField $inst final_status $bodyStr
    Set-HookFallbackJsonQuotedField $inst error_message $bodyStr
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookSessionEndInputBody]::new()

    if ($obj.PSObject.Properties["session_id"]) {
      $v = $obj.session_id
      if ($null -ne $v) {
        $inst.session_id = Get-PrettyUuid -Id ([string]$v)
      }
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["reason"]) {
      $v = $obj.reason
      if ($null -ne $v) {
        $inst.reason = [string]$v
      }
      $obj.PSObject.Properties.Remove("reason")
    }
    if ($obj.PSObject.Properties["duration_ms"]) {
      $v = $obj.duration_ms
      if ($null -ne $v) {
        $inst.duration_ms = [long]$v
      }
      $obj.PSObject.Properties.Remove("duration_ms")
    }
    if ($obj.PSObject.Properties["is_background_agent"]) {
      $inst.is_background_agent = [bool]$obj.is_background_agent
      $obj.PSObject.Properties.Remove("is_background_agent")
    }
    if ($obj.PSObject.Properties["final_status"]) {
      $v = $obj.final_status
      if ($null -ne $v) {
        $inst.final_status = [string]$v
      }
      $obj.PSObject.Properties.Remove("final_status")
    }
    if ($obj.PSObject.Properties["error_message"]) {
      $v = $obj.error_message
      if ($null -ne $v) {
        $inst.error_message = [string]$v
      }
      $obj.PSObject.Properties.Remove("error_message")
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
    $inst = [R2eHookSessionEndInputBody]::new()
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


# Hook: sessionEnd
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





