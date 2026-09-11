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
[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("1.0.0.0")]

public class PatchFile {
    public string relative, originalSha256, patchedSha256, patch, patchSha256;
    public long originalLength, patchedLength;
    public bool optional;
}
public class PatchManifest { public string version, gameVersion, scope; public PatchFile[] files; }
public class SetupState {
    public string version, gameRoot;
    public List<PatchFile> files = new List<PatchFile>();
    public Dictionary<string,string> configBefore = new Dictionary<string,string>();
}
public static class SupportEngine {
#if DATA_SUPPORT
    public const string Scope="data", BackupFolder="korean-data-backup", Label="기본 게임 데이터 한국어화";
#else
    public const string Scope="native", BackupFolder="korean-native-backup", Label="전체판 EXE·UI 한국어화";
#endif
    static void ValidateScope(IEnumerable<PatchFile> files) {
        foreach(var f in files) {
            bool data=Regex.IsMatch(f.relative,@"^(game|dlc/[^/]+)/Languages/English/WorldMap\.(ar\.00|arl)$");
            bool native=f.relative=="UnleashedRecomp.exe"||f.relative=="patched/default.xex";
            if(!(Scope=="data"?data:native))throw new Exception("설치 범위 밖의 파일입니다: "+f.relative);
        }
    }
    public static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength=16777216 };
    public static string Hash(byte[] bytes) { using(var h=SHA256.Create()) return BitConverter.ToString(h.ComputeHash(bytes)).Replace("-","").ToLowerInvariant(); }
    public static string HashFile(string path) { using(var h=SHA256.Create()) using(var f=File.OpenRead(path)) return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant(); }
    public static string Safe(string root, string relative) {
        if(String.IsNullOrEmpty(relative)||Path.IsPathRooted(relative)||relative.IndexOf(':')>=0) throw new Exception("잘못된 파일 경로입니다.");
        string boundary=Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        string path=Path.GetFullPath(Path.Combine(root,relative.Replace('/',Path.DirectorySeparatorChar)));
        if(!path.StartsWith(boundary,StringComparison.OrdinalIgnoreCase)) throw new Exception("설치 폴더 밖의 경로는 사용할 수 없습니다.");
        return path;
    }
    static void Atomic(string path, byte[] data) {
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        string temp=path+".kr-"+Guid.NewGuid().ToString("N")+".tmp";
        try { File.WriteAllBytes(temp,data); if(File.Exists(path)) File.Replace(temp,path,null); else File.Move(temp,path); }
        finally { if(File.Exists(temp))File.Delete(temp); }
    }
    static void SaveState(string path, SetupState state) { Atomic(path,new UTF8Encoding(false).GetBytes(Json.Serialize(state))); }
    static byte[] Apply(byte[] old, byte[] packed, PatchFile spec) {
        byte[] data;
        using(var src=new MemoryStream(packed)) using(var gz=new GZipStream(src,CompressionMode.Decompress)) using(var dst=new MemoryStream()) {
            byte[] chunk=new byte[65536];int n;
            while((n=gz.Read(chunk,0,chunk.Length))>0) { if(dst.Length+n>536870912)throw new Exception("패치 크기 오류");dst.Write(chunk,0,n); }
            data=dst.ToArray();
        }
        using(var stream=new MemoryStream(data)) using(var reader=new BinaryReader(stream)) {
            if(Encoding.ASCII.GetString(reader.ReadBytes(8))!="URKRDP1\0")throw new Exception("패치 형식 오류");
            long oldSize=reader.ReadInt64(), newSize=reader.ReadInt64(), controls=reader.ReadInt64(), differences=reader.ReadInt64();
            if(oldSize!=old.Length||oldSize!=spec.originalLength||newSize!=spec.patchedLength||newSize<0||newSize>268435456||controls<0||controls%24!=0||differences<0||40+controls+differences>data.Length)throw new Exception("패치 범위 오류");
            byte[] result=new byte[(int)newSize];long outPos=0,oldPos=0,diffPos=40+controls,extraPos=diffPos+differences;
            for(long c=40;c<40+controls;c+=24) {
                long add=BitConverter.ToInt64(data,(int)c),extra=BitConverter.ToInt64(data,(int)c+8),seek=BitConverter.ToInt64(data,(int)c+16);
                if(add<0||extra<0||add>newSize-outPos||extra>newSize-outPos-add||diffPos+add>40+controls+differences||extraPos+extra>data.Length)throw new Exception("패치 데이터 오류");
                for(long i=0;i<add;i++) { long at=oldPos+i;result[(int)(outPos+i)]=unchecked((byte)(data[(int)(diffPos+i)]+(at>=0&&at<old.Length?old[(int)at]:0))); }
                outPos+=add;oldPos+=add;diffPos+=add;
                Buffer.BlockCopy(data,(int)extraPos,result,(int)outPos,(int)extra);outPos+=extra;extraPos+=extra;oldPos+=seek;
            }
            if(outPos!=newSize||diffPos!=40+controls+differences||extraPos!=data.Length||Hash(result)!=spec.patchedSha256)throw new Exception("완성 파일 검증 실패: "+spec.relative);
            return result;
        }
    }
    static string ConfigValue(string text,string key) { var m=Regex.Match(text,"(?m)^"+Regex.Escape(key)+@"\s*=\s*(.*)$");return m.Success?m.Groups[1].Value.TrimEnd('\r'):null; }
    static string SetConfig(string text,string key,string value) {
        string pattern="(?m)^"+Regex.Escape(key)+@"\s*=.*\r?$";
        if(value==null)return Regex.Replace(text,pattern+@"\n?","");
        if(!Regex.IsMatch(text,pattern))throw new Exception("게임 설정 항목을 찾지 못했습니다: "+key);
        return Regex.Replace(text,pattern,key+" = "+value);
    }
    static Dictionary<string,string> Settings=new Dictionary<string,string>{{"Language","\"English\""},{"Subtitles","true"}};
    public static void Run(string package,string root,bool restore,Action<string> log) {
        package=Path.GetFullPath(package);root=Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
        if(Process.GetProcessesByName("UnleashedRecomp").Length>0)throw new Exception("게임을 종료한 뒤 다시 실행해 주세요.");
        if(!File.Exists(Safe(root,"UnleashedRecomp.exe")))throw new Exception("UnleashedRecomp.exe가 있는 게임 폴더를 선택해 주세요.");
        string support=Safe(root,BackupFolder),statePath=Safe(support,"state.json");
        SetupState state=File.Exists(statePath)?Json.Deserialize<SetupState>(File.ReadAllText(statePath)):new SetupState{gameRoot=root};
        if(!String.Equals(state.gameRoot,root,StringComparison.OrdinalIgnoreCase))throw new Exception("백업에 기록된 게임 폴더가 다릅니다.");
        var changes=new Dictionary<string,byte[]>();var originals=new Dictionary<string,byte[]>();
        string configPath=Safe(root,"config.toml");if(!File.Exists(configPath))throw new Exception("게임의 최초 설치를 완료한 뒤 다시 실행해 주세요. (config.toml 없음)");
        byte[] configOld=File.ReadAllBytes(configPath);string config=Encoding.UTF8.GetString(configOld).TrimStart('\uFEFF');
        if(restore) {
            if(!File.Exists(statePath))throw new Exception("이 설치 도구의 복원 백업이 없습니다.");
            ValidateScope(state.files);
            foreach(var f in state.files) {
                string target=Safe(root,f.relative),backup=Safe(support,"Original/"+f.relative);
                if(!File.Exists(target)||!File.Exists(backup)||HashFile(backup)!=f.originalSha256)throw new Exception("복원 파일 검증 실패: "+f.relative);
                string current=HashFile(target);if(current!=f.patchedSha256&&current!=f.originalSha256)throw new Exception("설치 후 다른 내용으로 변경된 파일입니다. 덮어쓰지 않았습니다: "+f.relative);
                changes[target]=File.ReadAllBytes(backup);
            }
        } else {
            var manifest=Json.Deserialize<PatchManifest>(File.ReadAllText(Safe(package,"Support/manifest.json")));
            if(manifest.scope!=Scope)throw new Exception("도구와 패치 종류가 일치하지 않습니다.");
            ValidateScope(manifest.files);
            ValidateScope(state.files);
            state.version=manifest.version;
            foreach(var f in manifest.files) {
                string target=Safe(root,f.relative);
                if(!File.Exists(target)) { if(f.optional&&!Directory.Exists(Safe(root,String.Join("/",f.relative.Split('/').Take(2))))) {log("미설치 DLC 건너뜀: "+f.relative);continue;}throw new Exception("필수 파일을 찾지 못했습니다: "+f.relative); }
                string current=HashFile(target);byte[] original=null;
                string backup=Safe(support,"Original/"+f.relative);
                if(File.Exists(backup)) {if(HashFile(backup)!=f.originalSha256)throw new Exception("기존 백업 검증 실패: "+f.relative);original=File.ReadAllBytes(backup);}
                if(current==f.originalSha256)original=File.ReadAllBytes(target);
                else if(current==f.patchedSha256) {
                    if(original==null) {
                        foreach(string folder in new[]{"korean-mod-backup-v030","korean-mod-backup-v040"}) {
                            string legacy=Safe(root,folder+"/"+f.relative);
                            if(File.Exists(legacy)&&HashFile(legacy)==f.originalSha256){original=File.ReadAllBytes(legacy);break;}
                        }
                        if(original==null)throw new Exception("기존 한글 패치가 있지만 원본 백업을 찾지 못했습니다. 이전 설치 도구로 원본 복원 후 설치해 주세요.");
                    }
                } else throw new Exception("지원하지 않는 버전 또는 다른 패치가 적용된 파일입니다: "+f.relative+"\nWindows x64 v1.0.3 원본이 필요합니다. 파일은 변경하지 않았습니다.");
                byte[] patch=File.ReadAllBytes(Safe(package,f.patch));if(Hash(patch)!=f.patchSha256)throw new Exception("다운로드한 패치가 손상되었습니다: "+f.patch);
                log("검증 및 준비: "+f.relative);byte[] result=Apply(original,patch,f);
                changes[target]=result;originals[f.relative]=original;
                var previous=state.files.FirstOrDefault(x=>x.relative==f.relative);
                if(previous!=null)state.files.Remove(previous);state.files.Add(f);
            }
        }
        // All inputs and outputs are verified before touching game files.
        foreach(var kv in originals) {
            string backup=Safe(support,"Original/"+kv.Key);
            if(!File.Exists(backup))Atomic(backup,kv.Value);
        }
        if(!restore)SaveState(statePath,state); // Recovery is possible even if the process is interrupted.
        var rollback=new Dictionary<string,byte[]>();
        try {
            foreach(var kv in changes) {byte[] prior=File.ReadAllBytes(kv.Key);Atomic(kv.Key,kv.Value);rollback[kv.Key]=prior;if(HashFile(kv.Key)!=Hash(kv.Value))throw new Exception("설치 파일 확인 실패");}
        } catch {
            foreach(var kv in rollback)Atomic(kv.Key,kv.Value);
            throw;
        }
        log(restore?Label+" 복원 완료. 다른 종류의 한국어 패치는 유지됩니다.":Label+" 설치 완료. 기본 HMM 모드도 활성화해 주세요.");
        log("다른 모드 목록과 세이브 파일은 변경하지 않았습니다.");
    }
}
public class SupportWindow : Form {
    TextBox path=new TextBox(),output=new TextBox();Button install=new Button(),restore=new Button(),browse=new Button();string package;
    public SupportWindow(string folder) {
        package=folder;Text="언리쉬드 리컴파일드 한국어 패치 · 1.0.0";ClientSize=new Size(780,625);Font=new Font("맑은 고딕",10);StartPosition=FormStartPosition.CenterScreen;FormBorderStyle=FormBorderStyle.FixedDialog;MaximizeBox=false;AutoScaleMode=AutoScaleMode.Dpi;BackColor=Color.FromArgb(246,247,249);

        var header=new Panel{Location=new Point(0,0),Size=new Size(780,170),BackColor=Color.White};
        var logo=new PictureBox{Location=new Point(24,17),Size=new Size(315,136),SizeMode=PictureBoxSizeMode.Zoom,BackColor=Color.White,Image=LoadLogo(folder)};
        var title=new Label{Text="언리쉬드 리컴파일드",Font=new Font("맑은 고딕",17,FontStyle.Bold),Location=new Point(366,31),Size=new Size(380,37)};
        var subtitle=new Label{Text="한국어 패치  ·  EXE/UI 추가 적용",Font=new Font("맑은 고딕",11,FontStyle.Bold),ForeColor=Color.FromArgb(31,96,178),Location=new Point(368,75),Size=new Size(370,29)};
        var target=new Label{Text="적용 대상  Unleashed Recompiled",Location=new Point(368,111),Size=new Size(370,24)};
        var credit=new Label{Text="Windows v1.0.3 전용  ·  만든이 nonunsaram",ForeColor=Color.DimGray,Location=new Point(368,137),Size=new Size(390,24)};
        header.Controls.AddRange(new Control[]{logo,title,subtitle,target,credit});

        var guideTitle=new Label{Text="적용 방법",Font=new Font("맑은 고딕",12,FontStyle.Bold),Location=new Point(24,190),Size=new Size(120,28)};
        var info=new Label{Text="1. UnleashedRecomp.exe를 선택합니다.\n2. '.exe 한국어화 적용' 버튼을 누르면 옵션 및 도전과제 UI 한국어화를 적용합니다.\n3. HedgeModManager에서 모드가 적용되었는지 확인 후 플레이합니다.",Location=new Point(26,224),Size=new Size(730,76)};
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
        if(args.Length>=3&&(args[0]=="--install"||args[0]=="--restore")) {
            try {SupportEngine.Run(args.Length>3?args[3]:package,args[1],args[0]=="--restore",s=>File.AppendAllText(args[2],s+Environment.NewLine));return 0;}
            catch(Exception e){File.AppendAllText(args[2],e.ToString()+Environment.NewLine);return 1;}
        }
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new SupportWindow(package));return 0;
    }
}
