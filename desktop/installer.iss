; ============================================================
; MarketCoreSoft - Inno Setup Installer Script
; 
; Prerequisites:
;   1. Run desktop\build.bat first to create the dist package
;   2. Install Inno Setup 6+ from https://jrsoftware.org/isinfo.php
;   3. Open this file in Inno Setup Compiler and click Build
;
; Output: desktop\output\MarketCoreSoft_Setup_0.4.0.exe
; ============================================================

#define MyAppName "MarketCoreSoft"
#define MyAppVersion "0.4.0"
#define MyAppPublisher "MarketCoreSoft"
#define MyAppURL "https://marketcoresoft.com"
#define MyAppExeName "MarketCoreSoft.bat"

[Setup]
AppId={{B8E2F1A0-4C3D-4E5F-9A1B-2C3D4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=MarketCoreSoft_Setup_{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Uncomment these lines if you create the icon/image files:
; SetupIconFile=assets\icon.ico
; UninstallDisplayIcon={app}\assets\icon.ico
; WizardImageFile=assets\wizard.bmp
; WizardSmallImageFile=assets\wizard_small.bmp

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el &Escritorio"; GroupDescription: "Accesos directos:"; Flags: checked
Name: "autostart"; Description: "Iniciar automáticamente con Windows"; GroupDescription: "Opciones:"; Flags: unchecked
Name: "firewall"; Description: "Configurar regla de Firewall (acceso desde red local)"; GroupDescription: "Red:"; Flags: checked

[Files]
Source: "dist\MarketCoreSoft\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MarketCoreSoft"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Detener MarketCoreSoft"; Filename: "{app}\Detener.bat"
Name: "{group}\Desinstalar MarketCoreSoft"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MarketCoreSoft"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Autostart entry (optional task)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "MarketCoreSoft"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Open firewall port for LAN access (optional task)
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""MarketCoreSoft"" dir=in action=allow protocol=TCP localport=443"; Flags: runhidden; Tasks: firewall
; Launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar MarketCoreSoft ahora"; Flags: nowait postinstall skipifsilent shellexec

[UninstallRun]
; Remove firewall rule on uninstall  
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""MarketCoreSoft"""; Flags: runhidden
