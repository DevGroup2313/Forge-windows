; THE FORGE  |  Copyright (c) 2026 Yannie D. Forest. All rights reserved.
; NO LICENCE IS GRANTED. See LICENCE.txt.
;
; The Windows installer, made by Inno Setup on GitHub's Windows computer
; (.github/workflows/build-windows-app.yml). You do not run this file yourself.
;
; It installs The Forge for the current user only (no administrator
; password) into %LOCALAPPDATA%\Programs\The Forge, puts it in the Start
; menu (and on the Desktop if ticked), and registers an uninstaller in
; Settings, Apps. Your work stays in %LOCALAPPDATA%\TheForge, a different
; folder that neither installing nor uninstalling ever deletes; before
; installing, a copy of it is made in %LOCALAPPDATA%\TheForge\backups
; (the three newest copies are kept).
;
; 9s57: an update always starts clean (the app's own record of an unfinished
; run is removed); uninstalling first asks a running copy to close the way its
; own close button does; a PC without Microsoft Edge WebView2 is told so on one
; calm page, with Microsoft's download page, and the install carries on; and
; the Ready page is gone, so the Shortcuts page's button says Install.
;
; The same design as Inkwell's Windows installer (Inkwell-Windows\build\
; inkwell.iss, Inkwell 7.36): every [Setup] key Inkwell sets is set here the
; same way, except the AppId (it must never change) and the installer's file
; name (kept the same, so its link never changes); the additions are named
; above and below. As for
; Inkwell, this installer is the only file the GitHub build publishes: the
; program folder it installs must stay together, so it is never handed out
; loose.
;
; The GitHub build passes these five values; the defaults below let the
; script also compile by hand beside a finished "dist" folder.

#ifndef AppVersion
  #define AppVersion "9s62"
#endif
#ifndef AppNumeric
  #define AppNumeric "1.0.0.0"
#endif
#ifndef ProgramDir
  #define ProgramDir "dist\The Forge"
#endif
#ifndef OutputDir
  #define OutputDir "dist"
#endif
#ifndef SetupName
  #define SetupName "the-forge-windows-setup"
#endif

[Setup]
AppId=com.yannieforest.theforge.windows
AppName=The Forge
AppVersion={#AppVersion}
AppVerName=The Forge {#AppVersion}
AppPublisher=Yannie D. Forest
AppCopyright=Copyright (c) 2026 Yannie D. Forest. All rights reserved.
VersionInfoVersion={#AppNumeric}
VersionInfoCompany=Yannie D. Forest
VersionInfoDescription=The Forge installer
VersionInfoProductName=The Forge
VersionInfoProductVersion={#AppNumeric}
VersionInfoCopyright=Copyright (c) 2026 Yannie D. Forest. All rights reserved.
DefaultDirName={localappdata}\Programs\The Forge
DefaultGroupName=The Forge
DisableProgramGroupPage=yes
DisableDirPage=yes
; 9s57: one click fewer. Inno Setup's manual (DisableReadyPage): "Setting this
; to yes does not automatically change the caption of the Next button on the
; new last pre-installation wizard page to Install. You must do so manually
; instead." CurPageChanged below does that on the Shortcuts (Tasks) page.
DisableReadyPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename={#SetupName}
SetupIconFile=the_forge.ico
UninstallDisplayIcon={app}\The Forge.exe
UninstallDisplayName=The Forge
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Put The Forge on the Desktop"; GroupDescription: "Shortcuts:"

[InstallDelete]
; A newer build may no longer carry every library an older one had. The
; program's own libraries are cleared before the new ones are copied, so an
; update leaves nothing stale behind. Your work is not in this folder.
Type: filesandordirs; Name: "{app}\_internal"
; 9s57: the app's own record of a run that has not finished (the session
; flag). An update starts clean: a run the update itself interrupted does not
; count as a bad ending. Only this one small file:
; your work beside it is not touched. ([InstallDelete] entries "are processed
; as the first step of installation"; a missing file is simply skipped.)
Type: files; Name: "{localappdata}\TheForge\storage\the_forge_session.flag"

[Files]
Source: "{#ProgramDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\The Forge"; Filename: "{app}\The Forge.exe"; WorkingDir: "{app}"; Comment: "The Forge {#AppVersion}"
Name: "{userdesktop}\The Forge"; Filename: "{app}\The Forge.exe"; WorkingDir: "{app}"; Comment: "The Forge {#AppVersion}"; Tasks: desktopicon

[Run]
Filename: "{app}\The Forge.exe"; Description: "Open The Forge now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; 9s57: if The Forge is open, ask it to close, NOT forcefully (no /F;
; Microsoft's taskkill page: "/f Specifies that processes be forcefully
; ended"). Closed the way its own close button closes it, the app records a
; clean ending; a forced end would leave the mark of a bad one. The [Code]
; below has already asked and waited (it runs first); this line is the
; uninstaller's own record of the same request. RunOnceId: run once even if
; the app was installed more than once (Inno Setup, [UninstallRun]); two
; quotes inside a quoted value make one (Inno Setup, Parameters).
Filename: "{sys}\taskkill.exe"; Parameters: "/IM ""The Forge.exe"""; Flags: runhidden; RunOnceId: "CloseTheForge"

[UninstallDelete]
; Builds before 9s58 wrote their record (and a test file) beside the program;
; without these lines the uninstaller would leave the program folder behind.
; Since 9s58 the record is kept beside your work, as Inkwell keeps its own.
Type: files; Name: "{app}\the_forge_crash.log"
Type: files; Name: "{app}\.the_forge_write_test"

[Code]
var
  WebView2Page: TOutputMsgWizardPage;
  WebView2Missing: Boolean;

{ 9s57: Microsoft's documented test for the Edge WebView2 Runtime ("Detect if
  a WebView2 Runtime is already installed", learn.microsoft.com/en-us/
  microsoft-edge/webview2/concepts/distribution): the pv value under one of
  these two keys, "present and defined with a version greater than 0.0.0.0".
  The first is the per-machine key on 64-bit Windows, the second the per-user
  key. This installer runs in 64-bit mode, where the Reg* functions read the
  64-bit view (Inno Setup, "64-bit Install Mode"), so the first key is named
  with WOW6432Node exactly as Microsoft writes it. The program itself makes
  the same test when it starts (the_forge_app.py, _webview2_runtime). }
function WebView2Present: Boolean;
var
  Version: String;
begin
  Result := False;
  Version := '';
  if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) then
    if (Trim(Version) <> '') and (Trim(Version) <> '0.0.0.0') then
      Result := True;
  if not Result then
  begin
    Version := '';
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) then
      if (Trim(Version) <> '') and (Trim(Version) <> '0.0.0.0') then
        Result := True;
  end;
end;

procedure OpenWebView2Download(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExecAsOriginalUser('open', 'https://developer.microsoft.com/microsoft-edge/webview2/consumer/', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

{ One calm page, shown only when WebView2 is missing, before the Shortcuts
  page. The install carries on either way: without WebView2 the app opens in
  the browser and says so. A check that fails counts as present, so this page
  never appears by mistake. }
procedure InitializeWizard;
var
  Button: TNewButton;
begin
  try
    WebView2Missing := not WebView2Present;
  except
    WebView2Missing := False;
  end;
  if WebView2Missing then
    Log('Microsoft Edge WebView2 Runtime: not found in the registry.')
  else
    Log('Microsoft Edge WebView2 Runtime: present (or not checkable).');
  WebView2Page := CreateOutputMsgPage(wpWelcome,
    'Microsoft Edge WebView2',
    'One free part of Windows is missing on this PC.',
    'The Forge draws its window with Microsoft Edge WebView2, a free part of Windows. It is not on this PC.' + #13#10#13#10 +
    'You can carry on. The Forge installs now, and opens in your browser until WebView2 is added.' + #13#10#13#10 +
    'To add it: open Microsoft''s page, click Download WebView2, and run the file. Then open The Forge again.' + #13#10#13#10 +
    'https://developer.microsoft.com/microsoft-edge/webview2/consumer/');
  Button := TNewButton.Create(WebView2Page);
  Button.Caption := 'Open Microsoft''s page';
  Button.Width := ScaleX(180);
  Button.Height := ScaleY(23);
  Button.Top := WebView2Page.MsgLabel.Top + WebView2Page.MsgLabel.Height + ScaleY(12);
  Button.OnClick := @OpenWebView2Download;
  Button.Parent := WebView2Page.Surface;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = WebView2Page.ID) and not WebView2Missing;
end;

{ With no Ready page, the Shortcuts page is the last one before installing,
  so its button says Install (see DisableReadyPage above). }
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectTasks then
    WizardForm.NextButton.Caption := SetupMessage(msgButtonInstall);
end;

{ True while The Forge is running. tasklist lists it by name (CSV, so a
  long name is never cut short) and find ends with 0 when the name is there.
  Both are named by their path in System32, so no other "find" on the PATH
  is used by mistake; if anything fails, the answer is "not running". }
function ProgramIsRunning: Boolean;
var
  Code: Integer;
begin
  Result := False;
  if Exec(ExpandConstant('{cmd}'), '/C ' + ExpandConstant('{sys}\tasklist.exe') + ' /FI "IMAGENAME eq The Forge.exe" /FO CSV /NH | ' +
          ExpandConstant('{sys}\find.exe') + ' /I "The Forge.exe"',
          '', SW_HIDE, ewWaitUntilTerminated, Code) then
    Result := (Code = 0);
end;

{ 9s57: uninstalling while The Forge is open. The uninstaller removes
  files straight after its [UninstallRun] entries and does not try again
  ("Failed to delete the file; it may be in use"), so a copy still closing
  would keep its program files. This step comes first (Inno Setup's
  Setup.Uninstall.pas calls CurUninstallStepChanged(usUninstall) before
  PerformUninstall, whose step 1 runs [UninstallRun]): it asks the app to
  close, not forcefully, and gives it up to 15 seconds to finish. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Code, Tries: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    if ProgramIsRunning then
    begin
      Exec(ExpandConstant('{sys}\taskkill.exe'), '/IM "The Forge.exe"', '', SW_HIDE, ewWaitUntilTerminated, Code);
      Tries := 0;
      while ProgramIsRunning and (Tries < 30) do
      begin
        Sleep(500);
        Tries := Tries + 1;
      end;
      if ProgramIsRunning then
        Log('The Forge was still open after 15 seconds; some of its files may stay until it closes.')
      else
        Log('The Forge closed before its files were removed.');
    end;
  end;
end;

{ Keeps the newest copies in backups and deletes the older setup-<date>
  copies, so they do not pile up with every update. The names carry the
  date and time, so sorting them sorts them by age. }
procedure KeepNewestBackups(Keep: Integer);
var
  Root: String;
  FindRec: TFindRec;
  Names: TStringList;
  I: Integer;
begin
  Root := ExpandConstant('{localappdata}\TheForge\backups');
  Names := TStringList.Create;
  try
    if FindFirst(Root + '\setup-*', FindRec) then
    begin
      try
        repeat
          if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0 then
            Names.Add(FindRec.Name);
        until not FindNext(FindRec);
      finally
        FindClose(FindRec);
      end;
    end;
    Names.Sort;
    for I := 0 to Names.Count - 1 - Keep do
      DelTree(Root + '\' + Names[I], True, True, True);
  finally
    Names.Free;
  end;
end;

{ Before anything changes: copy the folder that holds your work to
  backups\setup-<date>. A copy only; nothing is moved. The web view's
  caches are left out, because they are rebuilt by themselves. The three
  newest copies are kept. }
procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
  Src, Dst: String;
begin
  if CurStep = ssInstall then
  begin
    Src := ExpandConstant('{localappdata}\TheForge\storage');
    if DirExists(Src) then
    begin
      Dst := ExpandConstant('{localappdata}\TheForge\backups\setup-') + GetDateTimeString('yyyymmdd-hhnnss', #0, #0) + '\storage';
      Exec(ExpandConstant('{sys}\robocopy.exe'), '"' + Src + '" "' + Dst + '" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /XD Cache "Code Cache" GPUCache DawnCache GrShaderCache ShaderCache',
           '', SW_HIDE, ewWaitUntilTerminated, Code);
      try
        KeepNewestBackups(3);
      except
        Log('Older backups could not be tidied: ' + GetExceptionMessage);
      end;
    end;
  end;
end;
