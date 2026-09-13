import AppKit
import Foundation

struct Cover: Decodable {
    let repo: String
    let label: String
    let title: [String]
    let subtitle: [String]
    let fontSize: Double
    let background: String
    let output: String
}

func color(_ hex: UInt32) -> NSColor {
    NSColor(srgbRed: CGFloat((hex >> 16) & 255) / 255,
            green: CGFloat((hex >> 8) & 255) / 255,
            blue: CGFloat(hex & 255) / 255, alpha: 1)
}

func text(_ value: String, x: CGFloat, y: CGFloat, size: CGFloat,
          bold: Bool, ink: NSColor, width: CGFloat, tracking: CGFloat = 0) throws {
    guard let font = NSFont(name: bold ? "Arial-BoldMT" : "ArialMT", size: size) else {
        throw NSError(domain: "Cover", code: 1, userInfo: [NSLocalizedDescriptionKey: "Arial font missing"])
    }
    let style = NSMutableParagraphStyle()
    style.lineBreakMode = .byClipping
    let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: ink,
        .kern: tracking, .paragraphStyle: style]
    let line = NSAttributedString(string: value, attributes: attrs)
    guard line.size().width <= width else {
        throw NSError(domain: "Cover", code: 2, userInfo: [NSLocalizedDescriptionKey:
            "Text overflows: \(value), \(line.size().width) > \(width)"])
    }
    line.draw(at: NSPoint(x: x, y: y))
}

func render(_ c: Cover, width: Int, height: Int, filename: String, jpeg: Bool) throws {
    guard let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: width,
        pixelsHigh: height, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
        isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0),
        let context = NSGraphicsContext(bitmapImageRep: bitmap),
        let background = NSImage(contentsOfFile: c.background) else {
        throw NSError(domain: "Cover", code: 3)
    }
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = context
    let cg = context.cgContext
    cg.translateBy(x: 0, y: CGFloat(height))
    let scale = CGFloat(width) / 1280
    cg.scaleBy(x: scale, y: -scale)
    NSGraphicsContext.current = NSGraphicsContext(cgContext: cg, flipped: true)
    let logicalHeight = CGFloat(height) / scale
    color(0x14212b).setFill()
    NSRect(x: 0, y: 0, width: 1280, height: logicalHeight).fill()
    let artWidth = max(1280, logicalHeight * 2)
    background.draw(in: NSRect(x: (1280-artWidth)/2, y: 0, width: artWidth, height: artWidth/2),
        from: .zero, operation: .copy, fraction: 1, respectFlipped: true, hints: [.interpolation: NSImageInterpolation.high])
    let offset = (logicalHeight - 640)/2
    try text(c.label, x: 62, y: 64 + offset, size: 19, bold: true,
             ink: color(0xa3c5c9), width: 680, tracking: 2.0)
    color(0x91b5b9).setFill()
    NSRect(x: 62, y: 107 + offset, width: 76, height: 3).fill()
    let lineHeight = CGFloat(c.fontSize) * 1.16
    let blockHeight = CGFloat(c.title.count) * lineHeight
    let titleTop: CGFloat = 185 + offset
    for (i,line) in c.title.enumerated() {
        try text(line, x: 60, y: titleTop + CGFloat(i)*lineHeight,
                 size: CGFloat(c.fontSize), bold: true, ink: color(0xf5f3ed), width: 716)
    }
    let subtitleTop = max(420 + offset, titleTop + blockHeight + 30)
    for (i,line) in c.subtitle.enumerated() {
        try text(line, x: 62, y: subtitleTop + CGFloat(i)*33,
                 size: 25, bold: false, ink: color(0xc2cbd0), width: 704)
    }
    NSGraphicsContext.restoreGraphicsState()
    let properties: [NSBitmapImageRep.PropertyKey: Any] = jpeg ? [.compressionFactor: 0.92] : [:]
    guard let data = bitmap.representation(using: jpeg ? .jpeg : .png, properties: properties) else {
        throw NSError(domain: "Cover", code: 4)
    }
    try data.write(to: URL(fileURLWithPath: c.output).appendingPathComponent(filename))
}

let manifest = CommandLine.arguments[1]
let covers = try JSONDecoder().decode([Cover].self, from: Data(contentsOf: URL(fileURLWithPath: manifest)))
let base = URL(fileURLWithPath: manifest).deletingLastPathComponent()
func resolve(_ path: String) -> String {
    (path as NSString).isAbsolutePath ? path : base.appendingPathComponent(path).path
}
for source in covers {
    let cover = Cover(repo: source.repo, label: source.label, title: source.title,
        subtitle: source.subtitle, fontSize: source.fontSize,
        background: resolve(source.background), output: resolve(source.output))
    try FileManager.default.createDirectory(atPath: cover.output, withIntermediateDirectories: true)
    try render(cover, width: 2560, height: 1280, filename: "cover-v2.png", jpeg: false)
    try render(cover, width: 1280, height: 640, filename: "social-preview-v2.jpg", jpeg: true)
    try render(cover, width: 1200, height: 627, filename: "linkedin-v2.jpg", jpeg: true)
    print("Rendered \(cover.repo)")
}
