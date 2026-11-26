; Instalador de Tamacuychi para Windows (Inno Setup 6).
; Lo usa .github/workflows/windows.yml después de compilar con PyInstaller.
; A mano: iscc /DVersion=1.0.0 instalador.iss  (tras construir_exe.bat)

#ifndef Version
  #define Version "1.0.0"
#endif

[Setup]
AppId={{6B1E2A55-3C1D-4D7B-9E2A-7A0C0B9C5E21}
AppName=Tamacuychi
AppVersion={#Version}
AppVerName=Tamacuychi {#Version}
AppPublisher=Wazoskitekus
AppPublisherURL=https://github.com/Wazoskitekus/Cobayadeescritorio
DefaultDirName={localappdata}\Programs\Tamacuychi
DefaultGroupName=Tamacuychi
DisableProgramGroupPage=yes
; Se instala solo para el usuario: no pide permisos de administrador
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Tamacuychi-instalador-{#Version}
SetupIconFile=icono.ico
UninstallDisplayIcon={app}\Tamacuychi.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
Name: "inicio"; Description: "Que la cobaya aparezca al encender el ordenador"; GroupDescription: "Arranque:"

[Files]
Source: "dist\Tamacuychi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Tamacuychi"; Filename: "{app}\Tamacuychi.exe"
Name: "{group}\Desinstalar Tamacuychi"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Tamacuychi"; Filename: "{app}\Tamacuychi.exe"; Tasks: escritorio

[Registry]
; El mismo valor que activa el menú "Iniciar con Windows" del programa
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Tamacuychi"; ValueData: """{app}\Tamacuychi.exe"""; Flags: uninsdeletevalue; Tasks: inicio

[Run]
Filename: "{app}\Tamacuychi.exe"; Description: "Abrir Tamacuychi ahora"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM Tamacuychi.exe"; Flags: runhidden; RunOnceId: "CerrarTamacuychi"

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\Tamacuychi\sonidos48"
