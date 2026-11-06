import Foundation
import Vision

// Prints text found in a PNG as JSON, in image pixels with a top-left origin.
guard CommandLine.arguments.count > 1,
      let image = NSData(contentsOfFile: CommandLine.arguments[1]) else {
    FileHandle.standardError.write("usage: ocr <image>\n".data(using: .utf8)!)
    exit(2)
}

let handler = VNImageRequestHandler(data: image as Data, options: [:])
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.automaticallyDetectsLanguage = true
try handler.perform([request])

var out: [[String: Any]] = []
for observation in request.results ?? [] {
    guard let top = observation.topCandidates(1).first else { continue }
    let box = observation.boundingBox
    out.append([
        "text": top.string,
        "x": box.minX, "y": 1 - box.maxY, "w": box.width, "h": box.height,
        "confidence": top.confidence,
    ])
}
let data = try JSONSerialization.data(withJSONObject: out)
FileHandle.standardOutput.write(data)
