grammar RetrAction;

@header {
package com.mypalmike.retraction;
}


DecNum     : [0-9]+;
HexNum     : '$'[0-9A-F]+;
CharLit    : '\''.;
Identifier : [A-Z][A-Z_0-9]*;
DblQuote   : '"';
String     : '"'.*'"';
And        : 'AND';
Or         : 'OR';
Xor        : 'XOR';
Lsh        : 'LSH';
Rsh        : 'RSH';
Ampersand  : '&';
Percent    : '%';
Bang       : '!';
Equals     : '=';
Pound      : '#';
NotEqual   : '<>';
Lt         : '<';
LtEq       : '<=';
Gt         : '>';
GtEq       : '>=';
Plus       : '+';
Minus      : '-';
Times      : '*';
Div        : '/';
CharType   : 'CHAR';
CardType   : 'CARD';
ByteType   : 'BYTE';
IntType    : 'INT';
Define     : 'DEFINE';
Type       : 'TYPE';
Comma      : ',';
LBracket   : '[';
RBracket   : ']';
Pointer    : 'POINTER';
Array      : 'ARRAY';
AtSymbol   : '@';
LParen     : '(';
RParen     : ')';
Caret      : '^';
Dot        : '.';
Return     : 'RETURN';
Proc       : 'PROC';
Exit       : 'EXIT';
If         : 'IF';
Then       : 'THEN';
Else       : 'ELSE';
ElseIf     : 'ELSEIF';
Fi         : 'FI';
Do         : 'DO';
Until      : 'UNTIL';
Od         : 'OD';
For        : 'FOR';
To         : 'TO';
Step       : 'STEP';


program
    : Module progModule
    ;

progModule
    : systemDecls routineList
    ;

systemDecls
    : systemDecl*
    ;

systemDecl
    : defineDecl
    | typeDecl
    | fundVarDecl
    | pointerDecl
    | arrayDecl
    | recordDecl
    ;

defineDecl
    : Define definitionList
    ; 

definitionList
    : definition (Comma definition)*
    ;

definition
    : identifier Equals constant
    ;
    
typeDecl
    : Type recIdentList
    ;

recIdentList
    : recIdent+
    ;

recIdent
    : recName Equals LBracket fieldInit RBracket
    ;

recName
    : identifier
    ;

fieldInit
    : fundVarDecl
    ;

fundVarDecl
    : fundType fundIdentList
    ;

fundType
    : CardType
    | CharType
    | ByteType
    | IntType
    ;

fundIdentList
    : fundIdent (Comma fundIdent)*
    ;

fundIdent
    : identifier (Equals initOpts)?
    ;

initOpts
    : addr
    | LBracket value RBracket
    ;

addr
    : compConst
    ;

value
    : numConst
    ;

pointerDecl
    : ptrType Pointer ptrIdentList
    ;

ptrType
    : fundType
    | recName
    ;

ptrIdentList
    : ptrIdent (Comma ptrIdent)*
    ;
    
ptrIdent
    : identifier (Equals value)?
    ;

arrayDecl
    : fundType Array arrIdentList
    ;

arrIdentList
    : arrIdent (Comma arrIdent)*
    ;

arrIdent
    : identifier (dim)? (Equals arrInitOpts)?
    ;

dim
    : numConst
    ;

arrInitOpts
    : addr
    | LBracket arrValueList RBracket
    | stringConst
    ;

arrValueList
    : arrValue+
    ;
    
arrValue
    : compConst
    ;

recordDecl
    : identifier recordRecIdentList
    ;

recordRecIdentList
    : recordRecIdent (Comma recordRecIdent)*
    ;

recordRecIdent
    : identifier (Equals addr)
    ;

memReference
    : memContents
    | AtSymbol identifier
    ;

memContents
    : fundRef
    | arrRef
    | ptrRef
    | recRef
    ;    

fundRef
    : identifier
    ;

arrRef
    : identifier LParen arithExp RParen
    ;
    
ptrRef
    : identifier Caret
    ;
    
recRef
    : identifier Dot identifier
    ;

routineList
    : routine+
    ;
    
routine
    : procRoutine
    | funcRoutine
    ;

procRoutine
    : procDecl (systemDecls)? (stmtList)? (Return)?
    ;

procDecl
    : Proc identifier (Equals procAddr)? LParen (paramDecl)? RParen
    ;

procAddr
    : compConst
    ;

funcRoutine
    : funcDecl (systemDecls)? (stmtList)? (Return LParen arithExp RParen)?
    ;

funcDecl
    : fundType Func identifier (Equals funcAddr)? LParent (paramDecl)? RParen
    ;
    
funcAddr
    : compConst
    ;

routineCall
    : procCall
    | funcCall
    ;

procCall
    : identifier LParam (paramDecl) RParam
    ;

funcCall
    : identifier LParam (paramDecl) RParam
    ;
    
paramDecl
    : fundVarDecl
    ;

stmtList
    : stmt+
    ;

stmt
    : simpleStmt
    | strucStmt
    | codeBlock
    ;
    
simpleStmt
    : assignStmt
    | exitStmt
    | routineCall
    ;

strucStmt
    : ifStmt
    | doLoop
    | whileLoop
    | forLoop
    ;
    
assignStmt
    : memContents Equals arithExp
    ;

exitStmt
    : Exit
    ;

ifStmt
    : If condExp Then stmtList (elseifExten)? (Else stmt)? Fi
    ;

elseifExten
    : Elseif condExp Then (stmtList)?
    ;
    
elseExten
    : Else (stmtList)?
    ;
    
doLoop
    : Do (stmtList)? (untilStmt)? Od
    ;
    
untilStmt
    : Until condExp
    ;
    
whileLoop
    : While condExp doLoop
    ;
    
forLoop
    : For identifier Equals start To finish (Step inc) doLoop
    ;
    
start
    : arithExp
    ;
    
finish
    : arithExp
    ;
    
inc
    : arithExp
    ;

condExp
    : simpRelExp
    ;
    
codeBlock
    : LBracket compConstList RBracket
    ;
    
compConstList
    : compConst+
    ;
    
complexRel
    : complexRel specialOp simpRelExp
    | simpRelExp
    ;
    
simpRelExp
    : arithExp (relOp arithExp)*
    ;
    
arithExp
    : arithExp addOp multExp
    | multExp
    ;
    
multExp
    : multExp multOp multValue
    | multValue
    ;
    
multValue
    : numConst
    | memReference
    | LParen arithExp RParen
    ;

constant
    : numConst
    | stringConst
    | compConst
    ;
    
numConst
    : DecNum
    | HexNum
    | CharLit
    ;

stringConst
    : String
    ;
    
compConst
    : compConst Plus baseCompConst
    | baseCompConst
    ;
    
baseCompConst
    : identifier
    | numConst
    | ptrRef
    | Times
    ;
    
identifier
    : Identifier
    ;
    
// stringConst
//    : DblQuote String DblQuote
//   ;

specialOp
    : And
    | Or
    | Ampersand
    | Percent
    ;

relOp
    : Xor
    | Bang
    | Equals
    | Pound
    | NotEquals
    | Lt
    | LtEq
    | Gt
    | GtEq
    ;
    
addOp
    : Plus
    | Minus
    ;
    
multOp
    : Times
    | Divide
    | Mod
    | Lsh
    | Rsh
    ;
    
unaryOp
    : AtSymbol
    | Minus
    ;
    