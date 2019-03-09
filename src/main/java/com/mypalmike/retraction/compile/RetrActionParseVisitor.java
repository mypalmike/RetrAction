package com.mypalmike.retraction.compile;

import com.mypalmike.retraction.RetrActionBaseVisitor;
import com.mypalmike.retraction.RetrActionParser;
import com.mypalmike.retraction.ast.AstNode;

public class RetrActionParseVisitor extends RetrActionBaseVisitor<AstNode> {
    @Override
    public AstNode visitProgram(RetrActionParser.ProgramContext ctx) {

    }
}
