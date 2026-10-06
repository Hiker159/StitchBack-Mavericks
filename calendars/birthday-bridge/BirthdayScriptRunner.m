#import <Cocoa/Cocoa.h>
// Give Apple-event requests a stable app identity without changing TCC or Contacts.
static NSString *quote(NSString *s) {
    if ([s rangeOfCharacterFromSet:[NSCharacterSet controlCharacterSet]].location != NSNotFound) return nil;
    s = [s stringByReplacingOccurrencesOfString:@"\\" withString:@"\\\\"];
    s = [s stringByReplacingOccurrencesOfString:@"\"" withString:@"\\\""];
    return [NSString stringWithFormat:@"\"%@\"", s];
}
int main(int argc, const char **argv) {
    @autoreleasepool {
        [NSApplication sharedApplication];
        if (argc < 2) return 2;
        NSError *error = nil;
        NSString *path = [NSString stringWithUTF8String:argv[1]];
        NSString *source = [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:&error];
        if (!source) { fprintf(stderr, "%s\n", [[error description] UTF8String]); return 2; }
        if ([[source componentsSeparatedByString:@"on run argv"] count] != 2) {
            fprintf(stderr, "Expected one bridge entry handler\n"); return 2;
        }
        NSMutableArray *args = [NSMutableArray array];
        for (int i=2; i<argc; i++) {
            NSString *value = quote([NSString stringWithUTF8String:argv[i]]);
            if (!value) { fprintf(stderr,"Invalid argument\n"); return 2; }
            [args addObject:value];
        }
        source = [source stringByReplacingOccurrencesOfString:@"on run argv" withString:@"on bridgeRun(argv)"];
        source = [source stringByReplacingOccurrencesOfString:@"end run" withString:@"end bridgeRun"];
        source = [source stringByAppendingFormat:@"\nreturn my bridgeRun({%@})\n",[args componentsJoinedByString:@", "]];
        NSAppleScript *script = [[NSAppleScript alloc] initWithSource:source];
        NSDictionary *details = nil;
        NSAppleEventDescriptor *result = [script executeAndReturnError:&details];
        if (!result) {
            fprintf(stderr,"Birthday Bridge script error: %s\n",[[details description] UTF8String]);
            return 1;
        }
        NSString *value = [result stringValue];
        if (!value) { fprintf(stderr,"Expected text result\n"); return 1; }
        fprintf(stdout,"%s\n",[value UTF8String]);
        return 0;
    }
}
