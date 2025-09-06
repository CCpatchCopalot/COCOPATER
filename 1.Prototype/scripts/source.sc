import io.shiftleft.codepropertygraph.generated.nodes.* 

@main def exec(cpgFile: String, identifier_name: String, src_lines: String, dst_lines: List[Int], file: String): Unit = {
  importCpg(cpgFile)
  try {
     
    val srcArray = src_lines.split("\\|").map(_.toInt).toList
    var src = List.empty[Identifier]


    src = cpg.identifier.filter { node =>
      node.name.equals(identifier_name) &&
      node.lineNumber.exists(line => srcArray.contains(line))
    }.l


    if (src.isEmpty) {
      src = cpg.identifier.filter { node =>
        node.name.equals(identifier_name) &&
        node.lineNumber.exists(line => dst_lines.exists(dst => line < dst))
      }.l
    }

 
    val sink = cpg.identifier.filter { node =>
      node.name.equals(identifier_name) &&
      node.lineNumber.exists(line => dst_lines.contains(line))
    }.l


    sink.reachableByFlows(src).p |> s"${file}"
  } catch {
    case e: Exception => println("Couldn't parse that file.")
  }
}