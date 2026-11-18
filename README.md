# pairwise-archive-extract

压缩包导入功能一上线，解压就成了任意写文件入口：entry 名里的 ../ 直接拼到目标目录；绝对路径和 Windows 盘符不拦；符号链接先解出来再被后续 entry 写入；硬链接能指向宿主机文件；压缩比 1000:1 的炸弹不设上限；嵌套压缩包递归解压没有深度限制；文件名编码混用 UTF-8 和 CP437，归一后重复覆盖；同名 entry 后写覆盖先写；Unicode 同形字符绕过黑名单；tar 里的 device/FIFO 也照常创建；权限位保留 setuid；解压根目录可被 entry 改写；entry 数量不限制；加密包密码错误还继续解；失败后临时目录不清理。security/archive_extract.py 是核心，tests/test_archive_extract.py 15个红。要修的是：路径归一与根目录锁定；拒绝绝对路径；符号/硬链接；压缩比与总大小；递归深度；编码归一；重复 entry；Unicode 归一；特殊文件类型；权限清理；根目录不可变；entry 数量；加密包失败即停；临时目录清理。

## 运行

```bash
python -m pytest tests -q
```

初始状态：15 个用例失败。修复实现使全部用例通过，不要修改 `tests/` 下的测试。

子方向：漏洞检测与攻防；任务类型：Bugfix；语言/框架：Python 3, pytest；环境可复现等级：无外部依赖。
