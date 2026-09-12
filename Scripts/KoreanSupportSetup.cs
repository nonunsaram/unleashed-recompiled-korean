using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("Unleashed Recompiled Korean Translation Setup")]
[assembly: System.Reflection.AssemblyProduct("Unleashed Recompiled Korean Translation")]
[assembly: System.Reflection.AssemblyCompany("nonunsaram")]
[assembly: System.Reflection.AssemblyVersion("1.0.1.0")]
[assembly: System.Reflection.AssemblyFileVersion("1.0.1.0")]

public class SupportWindow : Form {
    TextBox path=new TextBox(),output=new TextBox();Button install=new Button(),restore=new Button(),browse=new Button();string package;
    public SupportWindow(string folder) {
        package=folder;Text="언리쉬드 리컴파일드 한국어 패치 · 1.0.1";ClientSize=new Size(780,625);Font=new Font("맑은 고딕",10);StartPosition=FormStartPosition.CenterScreen;FormBorderStyle=FormBorderStyle.FixedDialog;MaximizeBox=false;AutoScaleMode=AutoScaleMode.Dpi;BackColor=Color.FromArgb(246,247,249);

        var header=new Panel{Location=new Point(0,0),Size=new Size(780,170),BackColor=Color.White};
        var logo=new PictureBox{Location=new Point(24,17),Size=new Size(315,136),SizeMode=PictureBoxSizeMode.Zoom,BackColor=Color.White,Image=LoadLogo(folder)};
        var title=new Label{Text="언리쉬드 리컴파일드",Font=new Font("맑은 고딕",17,FontStyle.Bold),Location=new Point(366,31),Size=new Size(380,37)};
        var subtitle=new Label{Text="한국어 패치  ·  EXE/UI 추가 적용",Font=new Font("맑은 고딕",11,FontStyle.Bold),ForeColor=Color.FromArgb(31,96,178),Location=new Point(368,75),Size=new Size(370,29)};
        var target=new Label{Text="적용 대상  Unleashed Recompiled",Location=new Point(368,111),Size=new Size(370,24)};
        var credit=new Label{Text="Windows v1.0.3 전용  ·  만든이 nonunsaram",ForeColor=Color.DimGray,Location=new Point(368,137),Size=new Size(390,24)};
        header.Controls.AddRange(new Control[]{logo,title,subtitle,target,credit});

        var guideTitle=new Label{Text="적용 방법",Font=new Font("맑은 고딕",12,FontStyle.Bold),Location=new Point(24,190),Size=new Size(120,28)};
        var info=new Label{Text="1. 게임을 한 번 실행하여 초기 설정을 완료하고 종료합니다. Basic판은 필요 없습니다.\n2. UnleashedRecomp.exe를 선택하고 '.exe 한국어화 적용'을 누릅니다.\n3. HMM에서 Full 모드를 체크·저장합니다. 화면 언어 English, 자막 켜기를 확인하세요.",Location=new Point(26,224),Size=new Size(730,76)};
        var pathTitle=new Label{Text="UnleashedRecomp.exe 위치",Font=new Font("맑은 고딕",9,FontStyle.Bold),Location=new Point(24,316),Size=new Size(190,23)};
        path.SetBounds(24,342,622,29);browse.Text="찾아보기";browse.SetBounds(656,340,100,33);
        install.Text=".exe 한국어화 적용";install.SetBounds(24,391,232,44);restore.Text=".exe 원본 복원";restore.SetBounds(268,391,200,44);
        var statusTitle=new Label{Text="처리 내용",Font=new Font("맑은 고딕",9,FontStyle.Bold),Location=new Point(24,455),Size=new Size(100,23)};
        output.Multiline=true;output.ReadOnly=true;output.ScrollBars=ScrollBars.Vertical;output.BackColor=Color.White;output.SetBounds(24,480,732,121);
        Controls.AddRange(new Control[]{header,guideTitle,info,pathTitle,path,browse,install,restore,statusTitle,output});
        var dir=new DirectoryInfo(folder);while(dir!=null){if(File.Exists(Path.Combine(dir.FullName,"UnleashedRecomp.exe"))){path.Text=dir.FullName;break;}dir=dir.Parent;}
        browse.Click+=(s,e)=>{using(var d=new OpenFileDialog{Filter="Unleashed Recompiled|UnleashedRecomp.exe",Title="게임의 UnleashedRecomp.exe를 선택해 주세요"})if(d.ShowDialog()==DialogResult.OK)path.Text=Path.GetDirectoryName(d.FileName);};
        install.Click+=async(s,e)=>await Work(false);restore.Click+=async(s,e)=>await Work(true);
        FormClosing+=(s,e)=>{if(!install.Enabled)e.Cancel=true;};
    }
    static Image LoadLogo(string folder) {
        try {
            string external=Path.Combine(folder,"Support","InstallerLogo.png");
            if(File.Exists(external))using(var image=Image.FromFile(external))return new Bitmap(image);
            using(var stream=typeof(SupportWindow).Assembly.GetManifestResourceStream("UnleashedRecompiledLogo"))if(stream!=null)using(var image=Image.FromStream(stream))return new Bitmap(image);
        } catch { }
        return null;
    }
    async Task Work(bool undo) {
        install.Enabled=restore.Enabled=browse.Enabled=path.Enabled=false;output.Clear();string root=path.Text;
        Action<string> log=t=>BeginInvoke((Action)(()=>output.AppendText(t+Environment.NewLine)));
        try {await Task.Run(()=>SupportEngine.Run(package,root,undo,log));}
        catch(Exception e){output.AppendText("\r\n"+e.Message+"\r\n");}
        finally {install.Enabled=restore.Enabled=browse.Enabled=path.Enabled=true;}
    }
}
public static class KoreanSupportSetup {
    [STAThread] public static int Main(string[] args) {
        string package=AppDomain.CurrentDomain.BaseDirectory;
        if(args.Length==2&&args[0]=="--preview") { Application.EnableVisualStyles(); using(var form=new SupportWindow(package)) using(var bitmap=new Bitmap(form.Width,form.Height)) { form.Opacity=0; form.ShowInTaskbar=false; form.Show(); Application.DoEvents(); form.DrawToBitmap(bitmap,new Rectangle(0,0,bitmap.Width,bitmap.Height)); bitmap.Save(args[1],System.Drawing.Imaging.ImageFormat.Png); } return 0; }
        if(args.Length>=3&&(args[0]=="--install"||args[0]=="--restore"||args[0]=="--diagnose")) {
            var report=new StringBuilder();int result=0;
            try {
                string root=SupportEngine.GameRoot(args[1]);
                string logPath=Path.GetFullPath(args[2]);
                string boundary=root.TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
                if(logPath.StartsWith(boundary,StringComparison.OrdinalIgnoreCase))return 2; // Never write CLI logs into game data.
                if(args[0]=="--diagnose")SupportEngine.Diagnose(package,root,s=>report.AppendLine(s));
                else SupportEngine.Run(args.Length>3?args[3]:package,root,args[0]=="--restore",s=>report.AppendLine(s));
            } catch(Exception e){report.AppendLine(e.Message);result=1;}
            try {File.AppendAllText(args[2],report.ToString());}catch{return 2;}
            return result;
        }
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new SupportWindow(package));return 0;
    }
}
