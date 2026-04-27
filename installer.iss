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

[Icons]
Name: "{group}\Test de Bus Modbus Aviot"; Filename: "{app}\Test_Bus_Aviot.exe"
Name: "{autodesktop}\Test Bus Modbus Aviot"; Filename: "{app}\Test_Bus_Aviot.exe"

[Run]
Filename: "{app}\Test_Bus_Aviot.exe"; Flags: postinstall nowait skipifsilent
