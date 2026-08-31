#import <dispatch/dispatch.h>
#import <Foundation/Foundation.h>
#import <dlfcn.h>
#import <string.h>
#import <unistd.h>

/*
 * NoBTAudioReconnect v0.0.5（最终自解版）
 *
 * 实测结论（0.0.3 诊断版）：循环本体是
 *   xpc_connection_create_mach_service("com.apple.BTAudioHALPlugin.xpc")
 *   实测 ~6000 次/秒，由 BTAudioHALPlugin 在连接被沙箱拒绝后立即重开导致。
 * 对照实验（0.0.4）：hook dlopen 禁止插件加载后，launchd 占用回落到近 0。
 *
 * 本版 = 0.0.4 的静默化：
 *  - 保留 dlopen 拦截（KILL_LOAD），让插件根本进不了进程；
 *  - 日志严格限流（前 5 次后静默），避免 0.0.3 那种刷爆日志的假死。
 */

#define LOGF(...) do { NSLog(@"NBT: " __VA_ARGS__); } while(0)

extern void MSHookFunction(void *symbol, void *replace, void **result);

static void *(*o_dlopen)(const char *, int);
static long n_blocked;

static void *h_dlopen(const char *path, int mode)
{
    if (path && strstr(path, "BTAudioHALPlugin")) {
        n_blocked++;
        /* 只在 1/2/4/8/16 次打日志，之后完全静默 */
        if (n_blocked <= 16 && (n_blocked & (n_blocked - 1)) == 0)
            LOGF(@"blocked dlopen #%ld: %s", n_blocked, path);
        return NULL;
    }
    return o_dlopen(path, mode);
}

__attribute__((constructor))
static void NoBTAudioReconnect_init(void)
{
    LOGF(@"loaded pid=%d (kill-mode)", getpid());
    MSHookFunction((void *)dlopen, (void *)h_dlopen, (void **)&o_dlopen);
}
