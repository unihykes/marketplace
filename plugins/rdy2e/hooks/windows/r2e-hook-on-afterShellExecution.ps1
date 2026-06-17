param()

. (Join-Path $PSScriptRoot "r2e-hook-common.ps1")

class R2eHookAfterShellExecutionInputBody {
  [string]$session_id
  [string]$command
  [string]$output
  [long]$duration
  [bool]$sandbox
  [hashtable]$others

  R2eHookAfterShellExecutionInputBody() {
    $this.duration = 0
    $this.sandbox = $false
  }

  [string] ToJsonString() {
    $h = @{
      command    = $this.command
      output     = $this.output
      duration = $this.duration
      sandbox  = $this.sandbox
    }
    if ($null -ne $this.others -and $this.others.Count -gt 0) {
      $h.others = $this.others
    }
    return (ConvertTo-R2eHookEventLogJson -InputObject $h)
  }
}

function Set-AfterShellHookFallbackJsonLongField {
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
    return $head, ([R2eHookAfterShellExecutionInputBody]::new())
  }

  if (-not $head.IsValidJson) {
    $inst = [R2eHookAfterShellExecutionInputBody]::new()
    Set-HookFallbackJsonQuotedField $inst session_id $bodyStr -Convert { param($cap) Get-PrettyUuid -Id $cap }
    Set-HookFallbackJsonQuotedField $inst command $bodyStr -Convert { param($cap) '...' }
    Set-HookFallbackJsonQuotedField $inst output $bodyStr -Convert { param($cap) '...' }
    Set-AfterShellHookFallbackJsonLongField $inst duration $bodyStr
    Set-HookFallbackJsonBoolField $inst sandbox $bodyStr
    $inst.others = @{ _errorMessage = "invalid json" }
    return $head, $inst
  }

  try {
    $obj = $bodyStr | ConvertFrom-Json
    $inst = [R2eHookAfterShellExecutionInputBody]::new()

    if ($obj.PSObject.Properties["session_id"]) {
      $v = $obj.session_id
      if ($null -ne $v) {
        $inst.session_id = Get-PrettyUuid -Id ([string]$v)
      }
      $obj.PSObject.Properties.Remove("session_id")
    }
    if ($obj.PSObject.Properties["command"]) {
      $inst.command = '...'
      $obj.PSObject.Properties.Remove("command")
    }
    if ($obj.PSObject.Properties["output"]) {
      $inst.output = '...'
      $obj.PSObject.Properties.Remove("output")
    }
    if ($obj.PSObject.Properties["duration"]) {
      $v = $obj.duration
      if ($null -ne $v) {
        $inst.duration = [long]$v
      }
      $obj.PSObject.Properties.Remove("duration")
    }
    if ($obj.PSObject.Properties["sandbox"]) {
      $inst.sandbox = [bool]$obj.sandbox
      $obj.PSObject.Properties.Remove("sandbox")
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
    $inst = [R2eHookAfterShellExecutionInputBody]::new()
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


# Hook: afterShellExecution
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





