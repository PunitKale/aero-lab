param([string]$WorkbookPath)
$ErrorActionPreference = 'Stop'
$resolved = (Resolve-Path -LiteralPath $WorkbookPath).Path
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $book = $excel.Workbooks.Open($resolved)
    $excel.CalculateFullRebuild()
    $sheet = $book.Worksheets.Item('Python Reconciliation')
    $checks = @()
    for ($i=6; $i -le 10; $i++) {
        $difference = [double]$sheet.Cells.Item($i,4).Value2
        $checks += [pscustomobject]@{quantity=$sheet.Cells.Item($i,1).Value2;reference=$sheet.Cells.Item($i,2).Value2;excel_result=$sheet.Cells.Item($i,3).Value2;difference=$difference;passed=([math]::Abs($difference) -lt 0.000001)}
    }
    $book.Save()
    $checks | Export-Csv -LiteralPath (Join-Path (Split-Path $PSScriptRoot) 'reports/excel_reconciliation.csv') -NoTypeInformation
    $preview = Join-Path (Split-Path $PSScriptRoot) 'reports/workbook_preview.pdf'
    $overview=$book.Worksheets.Item('Lap Summary')
    $overview.PageSetup.PrintArea='$A$1:$H$30'
    $overview.ExportAsFixedFormat(0,$preview)
    $book.Close($true)
    $checks | Format-Table -AutoSize
} finally {
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
}
