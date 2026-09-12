using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using Microsoft.Win32.SafeHandles;

public class PatchFile {
    public string relative, originalSha256, patchedSha256, patch, patchSha256;
    public string[] previousPatchedSha256;
    public long originalLength, patchedLength;
}
public class PatchManifest {
    public int schemaVersion;
    public string version, gameVersion, scope;
    public PatchFile[] files;
}

// EXE-only backend. The embedded manifest, not mutable backup metadata, authorizes writes.
public static class SupportEngine {
    public const string BackupFolder="korean-native-backup", Label="전체판 EXE·UI 한국어화";
    const string Exe="UnleashedRecomp.exe";
    const long MaxFile=268435456;
    public static readonly JavaScriptSerializer Json=new JavaScriptSerializer {MaxJsonLength=1048576};
    public static string Hash(byte[] bytes) {using(var h=SHA256.Create())return Hex(h.ComputeHash(bytes));}
    public static string HashFile(string path) {using(var h=SHA256.Create())using(var f=OpenRead(path))return Hex(h.ComputeHash(f));}
    static string Hex(byte[] bytes) {return BitConverter.ToString(bytes).Replace("-","").ToLowerInvariant();}
    static bool IsHash(string s) {return s!=null&&Regex.IsMatch(s,@"\A[0-9a-f]{64}\z");}
    public static string GameRoot(string selection) {
        if(String.IsNullOrWhiteSpace(selection))throw new Exception("찾아보기에서 게임의 UnleashedRecomp.exe를 선택해 주세요.");
        string root=Path.GetFullPath(selection.Trim().Trim('"'));
        if(String.Equals(Path.GetFileName(root),Exe,StringComparison.OrdinalIgnoreCase))root=Path.GetDirectoryName(root);
        if(root!=Path.GetPathRoot(root))root=root.TrimEnd(Path.DirectorySeparatorChar);
        return root;
    }
    public static string Safe(string root,string relative) {
        if(String.IsNullOrEmpty(relative)||Path.IsPathRooted(relative)||relative.IndexOf(':')>=0)throw new Exception("잘못된 파일 경로입니다.");
        string boundary=Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        string path=Path.GetFullPath(Path.Combine(root,relative.Replace('/',Path.DirectorySeparatorChar)));
        if(!path.StartsWith(boundary,StringComparison.OrdinalIgnoreCase))throw new Exception("설치 폴더 밖의 경로는 사용할 수 없습니다.");
        return path;
    }
    static void NoLinks(string path) {
        for(string at=Path.GetFullPath(path);!String.IsNullOrEmpty(at);at=Path.GetDirectoryName(at)) {
            if((File.Exists(at)||Directory.Exists(at))&&(File.GetAttributes(at)&FileAttributes.ReparsePoint)!=0)
                throw new Exception("연결된 파일·폴더는 안전하게 변경할 수 없습니다. 실제 게임 폴더를 선택해 주세요: "+at);
        }
    }
    [StructLayout(LayoutKind.Sequential)] struct FileInfo {
        public uint attributes,creationLow,creationHigh,accessLow,accessHigh,writeLow,writeHigh,volume,sizeHigh,sizeLow,links,indexHigh,indexLow;
    }
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle handle,out FileInfo info);
    static FileStream OpenRead(string path) {
        NoLinks(path);
        var stream=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.Read);
        FileInfo info;
        if(!GetFileInformationByHandle(stream.SafeFileHandle,out info)||info.links!=1) {
            stream.Dispose();throw new Exception("파일의 연결 상태를 확인할 수 없거나 하드 링크입니다. 파일을 변경하지 않았습니다: "+path);
        }
        return stream;
    }
    static byte[] Read(string path,long limit=MaxFile) {
        using(var stream=OpenRead(path)) {
            if(stream.Length>limit)throw new Exception("예상보다 큰 파일입니다: "+path);
            byte[] data=new byte[(int)stream.Length];int offset=0,n;
            while(offset<data.Length&&(n=stream.Read(data,offset,data.Length-offset))>0)offset+=n;
            if(offset!=data.Length)throw new IOException("파일을 끝까지 읽지 못했습니다: "+path);
            return data;
        }
    }
    public static string ResolveConfigPath(string root) {
        if(File.Exists(Safe(root,"portable.txt"))||Directory.Exists(Safe(root,"portable.txt")))return Safe(root,"config.toml");
        string user=Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        if(String.IsNullOrEmpty(user))throw new Exception("Windows 사용자 설정 폴더를 찾을 수 없습니다. 게임과 같은 Windows 계정으로 실행해 주세요.");
        return Path.Combine(user,"UnleashedRecomp","config.toml");
    }
    public static void ValidateConfig(string text) {
        string section="";int sections=0;var values=new Dictionary<string,string>();
        foreach(string line in text.TrimStart('\uFEFF').Split('\n')) {
            var header=Regex.Match(line,@"^\s*\[([^\]]+)\]\s*(?:#.*)?$");
            if(header.Success){section=header.Groups[1].Value;if(section=="System")sections++;continue;}
            if(line.TrimStart().StartsWith("["))section="";
            if(section!="System")continue;
            var item=Regex.Match(line,@"^\s*(Language|Subtitles)\s*=\s*(.*?)\s*$");
            if(!item.Success)continue;
            string key=item.Groups[1].Value;
            if(values.ContainsKey(key))throw new Exception("지원하지 않는 config.toml 상태입니다. [System]의 "+key+" 항목이 중복되어 있습니다. 파일은 변경하지 않았습니다.");
            values.Add(key,item.Groups[2].Value);
        }
        foreach(string key in new[]{"Language","Subtitles"}) {
            string value;
            if(sections!=1||!values.TryGetValue(key,out value))throw new Exception("지원하지 않는 config.toml 상태입니다. [System]의 "+key+" 항목이 없거나 설정 구성이 예상과 다릅니다. 게임 버전과 설정 파일 상태를 확인해 주세요. 파일은 변경하지 않았습니다.");
            string pattern=key=="Language"?"^([\"'])(English|Japanese|German|French|Spanish|Italian)\\1\\s*(#.*)?$":@"^(true|false)\s*(#.*)?$";
            if(!Regex.IsMatch(value,pattern))throw new Exception("지원하지 않는 config.toml 상태입니다. [System]의 "+key+" 값이 예상과 다릅니다. 게임에서 설정을 확인하고 종료한 뒤 다시 실행해 주세요. 파일은 변경하지 않았습니다.");
        }
    }
    static void CheckConfig(string root,Action<string> log) {
        string path=ResolveConfigPath(root);
        if(!File.Exists(path))throw new Exception("게임 설정 파일(config.toml)을 찾을 수 없습니다. Unleashed Recompiled를 먼저 한 번 실행하여 초기 설정을 완료한 뒤 게임을 종료하고, 이 설치 도구를 다시 실행해 주세요.\nBasic판을 먼저 설치할 필요는 없습니다. 이미 게임을 실행한 적이 있다면 올바른 UnleashedRecomp.exe와 같은 Windows 계정인지 확인해 주세요.\n확인한 설정 파일 위치: "+path);
        ValidateConfig(new UTF8Encoding(false,true).GetString(Read(path,1048576)));
        log("게임 설정 확인 완료. 화면 언어 English, 자막 켜기를 확인해 주세요. 설정·음성 언어는 변경하지 않습니다.");
    }
    static byte[] ManifestBytes() {
        using(var resource=typeof(SupportEngine).Assembly.GetManifestResourceStream("KoreanFullManifest")) {
            if(resource==null)throw new Exception("설치 도구의 검증 정보가 없습니다. Full 패키지를 다시 받아 주세요.");
            using(var output=new MemoryStream()){resource.CopyTo(output);return output.ToArray();}
        }
    }
    static PatchManifest Manifest(byte[] bytes) {
        var m=Json.Deserialize<PatchManifest>(Encoding.UTF8.GetString(bytes).TrimStart('\uFEFF'));
        if(m==null||m.schemaVersion!=2||m.scope!="native-exe"||m.files==null||m.files.Length==0)throw new Exception("설치 도구의 검증 정보 형식이 잘못되었습니다.");
        var hashes=new HashSet<string>();
        foreach(var f in m.files) {
            if(f==null||f.relative!=Exe||!IsHash(f.originalSha256)||!IsHash(f.patchedSha256)||!IsHash(f.patchSha256)||
               f.originalSha256==f.patchedSha256||!hashes.Add(f.originalSha256)||
               f.originalLength<=0||f.originalLength>MaxFile||f.patchedLength<=0||f.patchedLength>MaxFile||
               f.patch==null||!Regex.IsMatch(f.patch,@"\ASupport/Patches/[A-Za-z0-9_-]+\.krpatch\.gz\z")||
               (f.previousPatchedSha256!=null&&f.previousPatchedSha256.Any(h=>!IsHash(h))))throw new Exception("설치 도구의 EXE 검증 정보가 잘못되었습니다.");
        }
        return m;
    }
    static bool Matches(PatchFile f,string hash) {return hash==f.originalSha256||hash==f.patchedSha256||(f.previousPatchedSha256!=null&&f.previousPatchedSha256.Contains(hash));}
    static void GameClosed(string root) {
        foreach(var process in Process.GetProcessesByName("UnleashedRecomp"))using(process) {
            try {if(String.Equals(Path.GetFullPath(process.MainModule.FileName),Safe(root,Exe),StringComparison.OrdinalIgnoreCase))throw new InvalidOperationException("선택한 게임이 실행 중입니다. 게임을 종료한 뒤 다시 실행해 주세요.");}
            catch(System.ComponentModel.Win32Exception){throw new Exception("게임 실행 상태를 확인할 수 없습니다. 실행 중인 Unleashed Recompiled를 종료한 뒤 다시 실행해 주세요.");}
        }
    }
    static byte[] Apply(byte[] original,byte[] packed,PatchFile spec) {
        byte[] data;
        using(var input=new MemoryStream(packed))using(var gzip=new GZipStream(input,CompressionMode.Decompress))using(var output=new MemoryStream()) {
            byte[] block=new byte[65536];int n;
            while((n=gzip.Read(block,0,block.Length))>0){if(output.Length+n>536870912)throw new Exception("패치 압축 해제 크기 오류");output.Write(block,0,n);}
            data=output.ToArray();
        }
        if(data.Length<40||Encoding.ASCII.GetString(data,0,8)!="URKRDP1\0")throw new Exception("패치 형식 오류");
        long oldSize=BitConverter.ToInt64(data,8),newSize=BitConverter.ToInt64(data,16),control=BitConverter.ToInt64(data,24),diff=BitConverter.ToInt64(data,32);
        if(oldSize!=original.Length||oldSize!=spec.originalLength||newSize!=spec.patchedLength||control<0||control%24!=0||diff<0||control>data.Length-40||diff>data.Length-40-control)throw new Exception("패치 범위 오류");
        byte[] result=new byte[(int)newSize];long outPos=0,oldPos=0,diffPos=40+control,extraPos=diffPos+diff;
        checked {
            for(long c=40;c<40+control;c+=24) {
                long add=BitConverter.ToInt64(data,(int)c),extra=BitConverter.ToInt64(data,(int)c+8),seek=BitConverter.ToInt64(data,(int)c+16);
                if(add<0||extra<0||add>newSize-outPos||extra>newSize-outPos-add||add>40+control+diff-diffPos||extra>data.Length-extraPos)throw new Exception("패치 데이터 오류");
                for(long i=0;i<add;i++){long at=oldPos+i;result[(int)(outPos+i)]=unchecked((byte)(data[(int)(diffPos+i)]+(at>=0&&at<original.Length?original[(int)at]:0)));}
                outPos+=add;oldPos+=add;diffPos+=add;
                Buffer.BlockCopy(data,(int)extraPos,result,(int)outPos,(int)extra);outPos+=extra;extraPos+=extra;oldPos+=seek;
            }
        }
        if(outPos!=newSize||diffPos!=40+control+diff||extraPos!=data.Length||Hash(result)!=spec.patchedSha256)throw new Exception("완성 EXE 검증 실패. 파일을 변경하지 않았습니다.");
        return result;
    }
    static void WriteNew(string path,byte[] bytes) {
        NoLinks(path);
        using(var stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None)){stream.Write(bytes,0,bytes.Length);stream.Flush(true);}
    }
    static void Fault(string point) {
#if TEST_FAULTS
        if(Environment.GetEnvironmentVariable("URKR_TEST_FAIL")==point)throw new IOException("테스트 실패: "+point);
        if(Environment.GetEnvironmentVariable("URKR_TEST_CRASH")==point)Environment.Exit(91);
#endif
    }
    static void InstallBackup(string path,byte[] original,string hash) {
        NoLinks(path);
        if(File.Exists(path)){if(HashFile(path)!=hash)throw new Exception("기존 백업 검증 실패. 백업을 덮어쓰지 않았습니다.");return;}
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        string temp=path+"."+Guid.NewGuid().ToString("N")+".tmp";
        try {WriteNew(temp,original);if(HashFile(temp)!=hash)throw new Exception("백업 저장 검증 실패");File.Move(temp,path);}
        finally {if(File.Exists(temp))File.Delete(temp);}
    }
    static void Commit(string target,string support,byte[] desired,string expected,Action<string> log) {
        string token=Guid.NewGuid().ToString("N"),staged=Safe(support,"exe-"+token+".tmp"),undo=Safe(support,"undo-"+token+".tmp");
        bool swapped=false,committed=false;
        try {
            WriteNew(staged,desired);
            if(HashFile(staged)!=Hash(desired))throw new IOException("임시 EXE 검증 실패");
            Fault("staged");
            if(HashFile(target)!=expected)throw new IOException("검사 중 EXE가 변경되었습니다. 다시 실행해 주세요.");
            NoLinks(target);NoLinks(support);
            Fault("before-swap");
            File.Replace(staged,target,undo,true);swapped=true;
            Fault("after-swap");
            if(HashFile(undo)!=expected||HashFile(target)!=Hash(desired))throw new IOException("EXE 교체 검증 실패");
            Fault("verified");
            committed=true;
        } catch {
            if(swapped) {
                try {
                    if(HashFile(target)!=Hash(desired))throw new IOException("교체 후 EXE가 다른 프로그램에 의해 변경되었습니다.");
                    string undoHash=HashFile(undo);
                    File.Replace(undo,target,null,true);
                    if(HashFile(target)!=undoHash)throw new IOException("교체 직전 EXE의 복구 검증 실패");
                    log("작업 실패로 교체 직전 EXE를 복구했습니다.");
                } catch(Exception rollback) {throw new Exception("자동 복구를 완료하지 못했습니다. 게임을 실행하지 말고 원본 복원을 실행해 주세요. 복구 파일: "+undo+"\n"+rollback.Message);}
            }
            throw;
        } finally {
            // Cleanup must never turn a successful commit into a reported failure,
            // or delete recovery evidence after failed rollback.
            try {if(File.Exists(staged))File.Delete(staged);if(committed&&File.Exists(undo))File.Delete(undo);}
            catch(IOException){log("임시 복구 파일 정리를 완료하지 못했습니다. 원본 백업은 유지됩니다.");}
            catch(UnauthorizedAccessException){log("임시 복구 파일 정리를 완료하지 못했습니다. 원본 백업은 유지됩니다.");}
        }
    }
    public static void Run(string package,string selection,bool restore,Action<string> log) {
        string root=GameRoot(selection),target=Safe(root,Exe);
        NoLinks(root);
        if(!File.Exists(target))throw new Exception("선택한 게임 폴더에서 UnleashedRecomp.exe를 찾을 수 없습니다. 찾아보기에서 올바른 게임 EXE를 선택해 주세요.");
        string key=Hash(Encoding.UTF8.GetBytes(root.ToUpperInvariant()));
        using(var mutex=new Mutex(false,"Local\\UnleashedKoreanFull-"+key)) {
            bool owned=false;
            try {
                try {owned=mutex.WaitOne(0);}catch(AbandonedMutexException){owned=true;}
                if(!owned)throw new Exception("이 게임 폴더에서 다른 Full 설치 도구가 작업 중입니다. 작업이 끝난 뒤 다시 실행해 주세요.");
                GameClosed(root);
                byte[] manifestBytes=ManifestBytes();var manifest=Manifest(manifestBytes);
                byte[] current=Read(target);string currentHash=Hash(current);
                var matches=manifest.files.Where(f=>Matches(f,currentHash)).ToArray();
                if(matches.Length!=1)throw new Exception("지원하지 않는 UnleashedRecomp.exe입니다. 이 도구는 공식 Windows x64 v1.0.3의 검증된 EXE와 지원되는 한국어 EXE만 처리합니다. 다른 버전·빌드 또는 다른 패치 여부를 확인해 주세요.\n확인한 SHA-256: "+currentHash+"\n파일은 변경하지 않았습니다.");
                var spec=matches[0];string support=Safe(root,BackupFolder),backup=Safe(support,"Original/"+Exe);
                // Old Full also changed XEX. An EXE-only restore must not leave
                // its translated text behind without the Korean native font.
                if(spec.previousPatchedSha256!=null&&spec.previousPatchedSha256.Contains(currentHash))
                    throw new Exception("이전 Full판의 EXE가 적용되어 있습니다. 이전 Full판 설치 도구에서 먼저 '.exe 원본 복원'을 실행한 뒤 v1.0.1을 설치해 주세요. 이전 도구가 처리하던 파일까지 복원해야 안전하게 전환할 수 있습니다. 백업 폴더는 삭제하지 마세요. 파일은 변경하지 않았습니다.");
                NoLinks(support);NoLinks(backup);
                if(!restore)CheckConfig(root,log);
                byte[] original=null;
                if(File.Exists(backup)) {
                    original=Read(backup);
                    if(Hash(original)!=spec.originalSha256||original.Length!=spec.originalLength)throw new Exception("기존 백업 검증 실패. 백업과 EXE를 덮어쓰지 않았습니다: "+backup);
                }
                if(currentHash==spec.originalSha256) {
                    if(current.Length!=spec.originalLength)throw new Exception("원본 EXE 크기 검증 실패");
                    original=current;
                    if(restore){log("이미 원본 EXE입니다. 변경할 파일이 없습니다.");return;}
                }
                if(original==null) {
                    foreach(string legacy in new[]{"korean-mod-backup-v030","korean-mod-backup-v040"}) {
                        string path=Safe(root,legacy+"/"+Exe);
                        if(File.Exists(path)){byte[] candidate=Read(path);if(candidate.Length==spec.originalLength&&Hash(candidate)==spec.originalSha256){original=candidate;break;}}
                    }
                    if(original==null)throw new Exception("한국어 EXE의 검증된 원본 백업을 찾지 못했습니다. 기존 백업 폴더를 복구하거나 공식 원본 EXE를 준비해 주세요. 파일은 변경하지 않았습니다.");
                }
                byte[] desired=original;
                if(!restore) {
                    package=Path.GetFullPath(package);
                    if(Hash(Read(Safe(package,"Support/manifest.json"),1048576))!=Hash(manifestBytes))throw new Exception("설치 도구와 패키지의 검증 정보가 다르거나 손상되었습니다. Full 패키지를 다시 받아 주세요.");
                    byte[] packed=Read(Safe(package,spec.patch),536870912);
                    if(Hash(packed)!=spec.patchSha256)throw new Exception("다운로드한 EXE 패치가 손상되었습니다. Full 패키지를 다시 받아 주세요.");
                    log("EXE 해시 확인 완료. 한국어 EXE를 준비합니다.");
                    desired=Apply(original,packed,spec);
                }
                // Only after all inputs/outputs pass validation may backup or EXE writes begin.
                InstallBackup(backup,original,spec.originalSha256);
                Fault("backup");
                if(Hash(desired)!=currentHash){GameClosed(root);Commit(target,support,desired,currentHash,log);}
                log(restore?"EXE 원본 복원 완료. HMM 모드의 기본 번역은 유지됩니다.":"전체판 EXE 설치 완료. HMM에서 Full 모드를 체크·저장해 주세요.");
                log("XEX·설정·음성 언어·다른 모드·세이브는 변경하지 않았습니다.");
            } catch(UnauthorizedAccessException e) {throw new Exception("파일 접근 권한이 없거나 읽기 전용입니다. 게임 폴더의 쓰기 권한과 보안 프로그램 차단 여부를 확인해 주세요.\n"+e.Message);}
              catch(IOException e) {throw new Exception("파일 작업을 완료하지 못했습니다. 게임과 파일을 사용하는 프로그램을 종료하고 저장 공간·권한을 확인해 주세요.\n"+e.Message);}
            finally {if(owned)mutex.ReleaseMutex();}
        }
    }
    public static void Diagnose(string package,string selection,Action<string> log) {
        string root=GameRoot(selection),target=Safe(root,Exe);var manifest=Manifest(ManifestBytes());
        log("읽기 전용 진단 · "+manifest.version);log("게임 폴더: "+root);
        log("EXE: "+(File.Exists(target)?HashFile(target):"없음"));
        string config=ResolveConfigPath(root);log("설정 경로: "+config);
        try{CheckConfig(root,log);}catch(Exception e){log(e.Message);}
        string backup=Safe(root,BackupFolder+"/Original/"+Exe);
        log("EXE 백업: "+(File.Exists(backup)?HashFile(backup):"없음"));
        log("진단 중 파일을 변경하지 않았습니다.");
    }
}
