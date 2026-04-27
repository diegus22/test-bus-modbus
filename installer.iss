[Setup]
AppName=Test de Bus Modbus Aviot
AppVersion=1.0
AppPublisher=Ingeniatic Desarrollo S.L.
AppPublisherURL=https://aviot.es
DefaultDirName={autopf}\Test Bus Modbus Aviot
DefaultGroupName=Aviot
OutputBaseFilename=Instalador_Test_Bus_Aviot
SetupIconFile=aviot.ico
WizardImageFile=wizard_image.bmp
WizardSmallImageFile=wizard_small.bmp
UninstallDisplayIcon={app}\Test_Bus_Aviot.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "dist\Test_Bus_Aviot.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "drivers\CH341SER.EXE"; DestDir: "{app}\drivers"; Flags: ignoreversion

[Icons]
Name: "{group}\Test de Bus Modbus Aviot"; Filename: "{app}\Test_Bus_Aviot.exe"
Name: "{autodesktop}\Test Bus Modbus Aviot"; Filename: "{app}\Test_Bus_Aviot.exe"

[Run]
; Siempre abre la app (con splash de instrucciones)
Filename: "{app}\Test_Bus_Aviot.exe"; Flags: postinstall nowait skipifsilent
; Solo abre el driver si NO está instalado
Filename: "{app}\drivers\CH341SER.EXE"; Flags: postinstall skipifsilent waituntilterminated; Check: not IsDriverInstalled

[Code]
function IsDriverInstalled: Boolean;
begin
  // Detecta driver CH340 en el registro de Windows
  Result := RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\CH341SER')
         or RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\CH341SER_A64');
end;
