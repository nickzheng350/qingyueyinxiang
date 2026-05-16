"""安全表达式求值模块 - 增强版"""

import ast
import sys
import types
from typing import Any, Dict, Optional, Set, Tuple, List
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """验证状态枚举"""
    VALID = "valid"
    SYNTAX_ERROR = "syntax_error"
    FORBIDDEN_NODE = "forbidden_node"
    UNDEFINED_VARIABLE = "undefined_variable"
    FORBIDDEN_FUNCTION = "forbidden_function"
    FORBIDDEN_ATTRIBUTE = "forbidden_attribute"
    TYPE_ERROR = "type_error"
    RUNTIME_ERROR = "runtime_error"


@dataclass
class ValidationResult:
    """验证结果"""
    status: ValidationStatus
    message: str
    node_type: Optional[str] = None
    line_number: Optional[int] = None
    column_offset: Optional[int] = None


@dataclass
class EvaluationResult:
    """求值结果"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    execution_time_ms: Optional[float] = None
    node_count: Optional[int] = None


class SafeExpressionEvaluator:
    """安全表达式求值器 - 基于 AST 解析的增强版"""

    # 允许的操作类型
    ALLOWED_NODE_TYPES = {
        ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp,
        ast.Compare, ast.Call, ast.Constant, ast.Name, ast.Attribute,
        ast.Subscript, ast.Slice, ast.Index, ast.ExtSlice,
        ast.List, ast.Tuple, ast.Dict, ast.Set,
    }

    # 允许的比较操作
    ALLOWED_COMPARE_OPS = (
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.Is, ast.IsNot, ast.In, ast.NotIn,
    )

    # 允许的二元操作
    ALLOWED_BIN_OPS = (
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
        ast.Pow, ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor,
    )

    # 允许的一元操作
    ALLOWED_UNARY_OPS = (
        ast.Invert, ast.Not, ast.UAdd, ast.USub,
    )

    # 允许的布尔操作
    ALLOWED_BOOL_OPS = (ast.And, ast.Or)

    # 允许的内置函数（白名单）
    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'chr', 'complex', 'divmod',
        'float', 'hash', 'hex', 'int', 'len', 'max', 'min', 'oct',
        'ord', 'pow', 'range', 'round', 'sum', 'str', 'type',
        'isinstance', 'issubclass', 'enumerate', 'reversed', 'sorted',
        'list', 'tuple', 'set', 'dict', 'slice', 'zip', 'range',
    }

    # 禁止的属性访问（黑名单）
    FORBIDDEN_ATTRS = {
        '__import__', '__subclasses__', '__bases__', '__globals__',
        '__code__', '__func__', '__self__', '__module__', '__class__',
        '__dict__', '__getattribute__', '__setattr__', '__delattr__',
        '__new__', '__init__', '__call__', '__repr__', '__str__',
        '__reduce__', '__reduce_ex__', '__getstate__', '__setstate__',
        '__format__', '__sizeof__', '__dir__', '__eq__', '__ne__',
        '__lt__', '__le__', '__gt__', '__ge__', '__hash__', '__bool__',
        '__instancecheck__', '__subclasscheck__', 'system', 'popen',
        'exec', 'eval', 'compile', 'open', 'file', 'input', 'raw_input',
        'breakpoint', 'help', 'quit', 'exit',
    }

    # 安全限制
    MAX_EXPRESSION_LENGTH = 1024
    MAX_NESTING_DEPTH = 100
    MAX_NODE_COUNT = 1000
    MAX_EXECUTION_TIME_MS = 5000

    def __init__(self):
        self._node_count = 0
        self._nesting_depth = 0
        self._validation_results: List[ValidationResult] = []

    def _check_limits(self) -> None:
        """检查安全限制"""
        if self._node_count > self.MAX_NODE_COUNT:
            raise ValueError(f"表达式节点数量超限: {self._node_count} > {self.MAX_NODE_COUNT}")
        if self._nesting_depth > self.MAX_NESTING_DEPTH:
            raise ValueError(f"表达式嵌套深度超限: {self._nesting_depth} > {self.MAX_NESTING_DEPTH}")

    def _validate_node(self, node: ast.AST, allowed_vars: Set[str]) -> None:
        """递归验证 AST 节点"""
        node_type = type(node)
        
        # 跳过上下文标记节点和操作符节点
        SKIP_NODE_TYPES = (
            ast.Load, ast.Store, ast.Del,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Is, ast.IsNot, ast.In, ast.NotIn,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
            ast.Pow, ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor,
            ast.Invert, ast.Not, ast.UAdd, ast.USub, ast.And, ast.Or,
        )
        if node_type in SKIP_NODE_TYPES:
            return

        # 计数和深度检查
        self._node_count += 1
        self._nesting_depth += 1
        self._check_limits()

        try:
            # 检查节点类型是否允许
            if node_type not in self.ALLOWED_NODE_TYPES:
                self._validation_results.append(ValidationResult(
                    status=ValidationStatus.FORBIDDEN_NODE,
                    message=f"不允许的表达式类型: {node_type.__name__}",
                    node_type=node_type.__name__,
                    line_number=getattr(node, 'lineno', None),
                    column_offset=getattr(node, 'col_offset', None)
                ))
                raise ValueError(f"不允许的表达式类型: {node_type.__name__}")

            # 检查变量访问
            if isinstance(node, ast.Name):
                if node.id not in allowed_vars and node.id not in self.ALLOWED_BUILTINS:
                    self._validation_results.append(ValidationResult(
                        status=ValidationStatus.UNDEFINED_VARIABLE,
                        message=f"未定义的变量: {node.id}",
                        node_type='Name',
                        line_number=node.lineno,
                        column_offset=node.col_offset
                    ))
                    raise ValueError(f"未定义的变量: {node.id}")

            # 检查属性访问 - 深度安全检查
            elif isinstance(node, ast.Attribute):
                # 禁止危险属性
                if isinstance(node.attr, str):
                    if node.attr in self.FORBIDDEN_ATTRS:
                        self._validation_results.append(ValidationResult(
                            status=ValidationStatus.FORBIDDEN_ATTRIBUTE,
                            message=f"禁止访问危险属性: {node.attr}",
                            node_type='Attribute',
                            line_number=node.lineno,
                            column_offset=node.col_offset
                        ))
                        raise ValueError(f"禁止访问危险属性: {node.attr}")
                    # 检查属性名是否以双下划线开头（dunder属性）
                    if node.attr.startswith('__'):
                        self._validation_results.append(ValidationResult(
                            status=ValidationStatus.FORBIDDEN_ATTRIBUTE,
                            message=f"禁止访问私有属性: {node.attr}",
                            node_type='Attribute',
                            line_number=node.lineno,
                            column_offset=node.col_offset
                        ))
                        raise ValueError(f"禁止访问私有属性: {node.attr}")
                self._validate_node(node.value, allowed_vars)

            # 检查函数调用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id not in self.ALLOWED_BUILTINS:
                        self._validation_results.append(ValidationResult(
                            status=ValidationStatus.FORBIDDEN_FUNCTION,
                            message=f"不允许调用函数: {node.func.id}",
                            node_type='Call',
                            line_number=node.lineno,
                            column_offset=node.col_offset
                        ))
                        raise ValueError(f"不允许调用函数: {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.attr, str) and node.func.attr in self.FORBIDDEN_ATTRS:
                        self._validation_results.append(ValidationResult(
                            status=ValidationStatus.FORBIDDEN_ATTRIBUTE,
                            message=f"禁止调用方法: {node.func.attr}",
                            node_type='Attribute',
                            line_number=node.func.lineno,
                            column_offset=node.func.col_offset
                        ))
                        raise ValueError(f"禁止调用方法: {node.func.attr}")
                    self._validate_node(node.func, allowed_vars)
                
                # 递归检查参数
                for arg in node.args:
                    self._validate_node(arg, allowed_vars)
                for kwarg in node.keywords:
                    self._validate_node(kwarg.value, allowed_vars)

            # 检查比较操作
            elif isinstance(node, ast.Compare):
                self._validate_node(node.left, allowed_vars)
                for op in node.ops:
                    if type(op) not in self.ALLOWED_COMPARE_OPS:
                        raise ValueError(f"不允许的比较操作: {type(op).__name__}")
                for comparator in node.comparators:
                    self._validate_node(comparator, allowed_vars)

            # 检查二元操作
            elif isinstance(node, ast.BinOp):
                if type(node.op) not in self.ALLOWED_BIN_OPS:
                    raise ValueError(f"不允许的二元操作: {type(node.op).__name__}")
                self._validate_node(node.left, allowed_vars)
                self._validate_node(node.right, allowed_vars)

            # 检查一元操作
            elif isinstance(node, ast.UnaryOp):
                if type(node.op) not in self.ALLOWED_UNARY_OPS:
                    raise ValueError(f"不允许的一元操作: {type(node.op).__name__}")
                self._validate_node(node.operand, allowed_vars)

            # 检查布尔操作
            elif isinstance(node, ast.BoolOp):
                if type(node.op) not in self.ALLOWED_BOOL_OPS:
                    raise ValueError(f"不允许的布尔操作: {type(node.op).__name__}")
                for value in node.values:
                    self._validate_node(value, allowed_vars)

            # 递归检查子节点
            for child in ast.iter_child_nodes(node):
                self._validate_node(child, allowed_vars)

        finally:
            self._nesting_depth -= 1

    def _validate_expression(self, expression: str) -> Tuple[ast.AST, ValidationResult]:
        """验证表达式语法（仅做基本语法检查，详细安全检查在 AST 验证阶段）"""
        # 长度检查
        if len(expression) > self.MAX_EXPRESSION_LENGTH:
            result = ValidationResult(
                status=ValidationStatus.SYNTAX_ERROR,
                message=f"表达式长度超限: {len(expression)} > {self.MAX_EXPRESSION_LENGTH}"
            )
            return None, result

        try:
            # 解析表达式（仅检查语法）
            tree = ast.parse(expression, mode='eval')
            
            return tree, ValidationResult(status=ValidationStatus.VALID, message="语法验证通过")
            
        except SyntaxError as e:
            result = ValidationResult(
                status=ValidationStatus.SYNTAX_ERROR,
                message=f"语法错误: {e.msg}",
                line_number=e.lineno,
                column_offset=e.offset
            )
            return None, result

    def _contains_malicious_pattern(self, expression: str) -> bool:
        """检查表达式是否包含恶意模式"""
        malicious_patterns = [
            # 代码注入模式
            r'__import__\s*\(',
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\bcompile\s*\(',
            r'\bopen\s*\(',
            r'\bsubprocess\s*\.',
            r'\bos\s*\.',
            # 反射攻击模式
            r'__class__',
            r'__bases__',
            r'__subclasses__',
            r'__globals__',
            r'__code__',
            r'__reduce__',
            # 命令执行模式
            r'system\s*\(',
            r'popen\s*\(',
            r'call\s*\(',
            r'spawn\s*\(',
            # 文件系统访问
            r'/etc/passwd',
            r'/etc/shadow',
            r'/root/',
            r'rm\s+-',
        ]
        
        import re
        for pattern in malicious_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return True
        return False

    def _validate_runtime_types(self, variables: Dict[str, Any]) -> None:
        """验证运行时变量类型安全"""
        for name, value in variables.items():
            # 禁止函数和类类型
            if isinstance(value, (types.FunctionType, types.MethodType, type)):
                raise ValueError(f"变量 {name} 包含不允许的类型: {type(value).__name__}")
            # 禁止模块类型
            if isinstance(value, types.ModuleType):
                raise ValueError(f"变量 {name} 包含不允许的模块类型")
            # 检查递归结构深度
            self._check_recursive_structure(value, name)

    def _check_recursive_structure(self, value: Any, name: str, depth: int = 0) -> None:
        """检查递归结构深度"""
        if depth > self.MAX_NESTING_DEPTH:
            raise ValueError(f"变量 {name} 嵌套深度超限")
        
        if isinstance(value, (list, tuple)):
            for item in value:
                self._check_recursive_structure(item, name, depth + 1)
        elif isinstance(value, dict):
            for key, val in value.items():
                self._check_recursive_structure(key, name, depth + 1)
                self._check_recursive_structure(val, name, depth + 1)

    def evaluate(self, expression: str, variables: Optional[Dict[str, Any]] = None) -> EvaluationResult:
        """
        安全地求值表达式（增强版）
        
        :param expression: 要求值的表达式字符串
        :param variables: 允许访问的变量字典
        :return: EvaluationResult 对象
        """
        import time
        
        variables = variables or {}
        self._node_count = 0
        self._nesting_depth = 0
        self._validation_results = []
        
        start_time = time.time()
        
        try:
            # 1. 表达式长度检查
            if len(expression) > self.MAX_EXPRESSION_LENGTH:
                return EvaluationResult(
                    success=False,
                    error=f"表达式长度超限",
                    validation_result=ValidationResult(
                        status=ValidationStatus.SYNTAX_ERROR,
                        message=f"表达式长度超限: {len(expression)} > {self.MAX_EXPRESSION_LENGTH}"
                    ),
                    execution_time_ms=0,
                    node_count=0
                )

            # 2. 语法验证
            tree, validation_result = self._validate_expression(expression)
            if validation_result.status != ValidationStatus.VALID:
                return EvaluationResult(
                    success=False,
                    error=validation_result.message,
                    validation_result=validation_result,
                    execution_time_ms=0,
                    node_count=0
                )

            # 3. 恶意模式快速检查（作为第一道防线）
            if self._contains_malicious_pattern(expression):
                return EvaluationResult(
                    success=False,
                    error="表达式包含潜在危险模式",
                    validation_result=ValidationResult(
                        status=ValidationStatus.FORBIDDEN_NODE,
                        message="表达式包含潜在危险模式"
                    ),
                    execution_time_ms=0,
                    node_count=0
                )

            # 4. 运行时类型验证
            self._validate_runtime_types(variables)

            # 5. AST 节点验证（详细安全检查）
            try:
                self._validate_node(tree, set(variables.keys()))
            except ValueError as e:
                # 根据错误信息判断具体的错误类型
                error_msg = str(e)
                status = ValidationStatus.FORBIDDEN_NODE
                if "未定义的变量" in error_msg:
                    status = ValidationStatus.UNDEFINED_VARIABLE
                elif "不允许调用函数" in error_msg:
                    status = ValidationStatus.FORBIDDEN_FUNCTION
                elif "禁止访问危险属性" in error_msg or "禁止访问私有属性" in error_msg:
                    status = ValidationStatus.FORBIDDEN_ATTRIBUTE
                raise ValueError(f"[{status.value}] {error_msg}")

            # 5. 构建安全的全局命名空间
            safe_globals = {}
            for name in self.ALLOWED_BUILTINS:
                if hasattr(__builtins__, name):
                    safe_globals[name] = getattr(__builtins__, name)
                elif name in __builtins__:
                    safe_globals[name] = __builtins__[name]

            # 6. 执行表达式（带超时控制）
            import threading
            result_container = []
            exception_container = []
            
            def execute():
                try:
                    result_container.append(eval(compile(tree, '<string>', 'eval'), safe_globals, variables))
                except Exception as e:
                    exception_container.append(e)
            
            thread = threading.Thread(target=execute)
            thread.daemon = True
            thread.start()
            thread.join(timeout=self.MAX_EXECUTION_TIME_MS / 1000)
            
            if thread.is_alive():
                return EvaluationResult(
                    success=False,
                    error=f"表达式执行超时",
                    validation_result=ValidationResult(
                        status=ValidationStatus.RUNTIME_ERROR,
                        message=f"执行超时: 超过 {self.MAX_EXECUTION_TIME_MS}ms"
                    ),
                    execution_time_ms=self.MAX_EXECUTION_TIME_MS,
                    node_count=self._node_count
                )
            
            if exception_container:
                return EvaluationResult(
                    success=False,
                    error=str(exception_container[0]),
                    validation_result=ValidationResult(
                        status=ValidationStatus.RUNTIME_ERROR,
                        message=str(exception_container[0])
                    ),
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    node_count=self._node_count
                )

            # 7. 结果类型检查
            result = result_container[0]
            self._validate_result_type(result)

            execution_time_ms = int((time.time() - start_time) * 1000)

            return EvaluationResult(
                success=True,
                result=result,
                validation_result=ValidationResult(
                    status=ValidationStatus.VALID,
                    message="执行成功"
                ),
                execution_time_ms=execution_time_ms,
                node_count=self._node_count
            )

        except ValueError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_str = str(e)
            
            # 解析状态信息
            status = ValidationStatus.FORBIDDEN_NODE
            message = error_str
            
            # 检查是否包含状态标记
            if error_str.startswith('['):
                end_bracket = error_str.find(']')
                if end_bracket > 0:
                    status_str = error_str[1:end_bracket]
                    message = error_str[end_bracket + 2:] if end_bracket + 2 < len(error_str) else ""
                    try:
                        status = ValidationStatus(status_str)
                    except ValueError:
                        pass
            
            return EvaluationResult(
                success=False,
                error=message,
                validation_result=ValidationResult(
                    status=status,
                    message=message
                ),
                execution_time_ms=execution_time_ms,
                node_count=self._node_count
            )
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return EvaluationResult(
                success=False,
                error=f"未知错误: {e}",
                validation_result=ValidationResult(
                    status=ValidationStatus.RUNTIME_ERROR,
                    message=str(e)
                ),
                execution_time_ms=execution_time_ms,
                node_count=self._node_count
            )

    def _validate_result_type(self, result: Any) -> None:
        """验证结果类型安全性"""
        # 禁止返回函数、类、模块等危险类型
        dangerous_types = (
            types.FunctionType, types.MethodType, type,
            types.ModuleType, types.CodeType
        )
        if isinstance(result, dangerous_types):
            raise ValueError(f"表达式返回了不允许的类型: {type(result).__name__}")


# 便捷函数
def safe_eval(expression: str, **variables) -> Any:
    """
    安全求值表达式的便捷函数
    
    使用示例:
    >>> safe_eval('item > 10', item=15)
    True
    >>> safe_eval('item * 2 + 1', item=5)
    11
    """
    evaluator = SafeExpressionEvaluator()
    result = evaluator.evaluate(expression, variables)
    if result.success:
        return result.result
    raise ValueError(result.error)


def safe_eval_with_result(expression: str, **variables) -> EvaluationResult:
    """
    安全求值表达式并返回完整结果对象
    
    :return: EvaluationResult 对象，包含详细的执行信息
    """
    evaluator = SafeExpressionEvaluator()
    return evaluator.evaluate(expression, variables)


def validate_expression(expression: str, allowed_vars: Optional[Set[str]] = None) -> ValidationResult:
    """
    仅验证表达式，不执行
    
    :param expression: 要验证的表达式字符串
    :param allowed_vars: 允许的变量名集合
    :return: ValidationResult 对象
    """
    evaluator = SafeExpressionEvaluator()
    return evaluator._validate_expression(expression)[1]


def analyze_expression(expression: str, **variables) -> Dict[str, Any]:
    """
    分析表达式的结构和潜在风险
    
    :return: 分析报告字典
    """
    import time
    
    start_time = time.time()
    
    evaluator = SafeExpressionEvaluator()
    result = evaluator.evaluate(expression, variables)
    
    analysis = {
        'expression': expression,
        'variables': list(variables.keys()),
        'success': result.success,
        'result': result.result if result.success else None,
        'error': result.error,
        'node_count': result.node_count,
        'execution_time_ms': result.execution_time_ms,
        'status': result.validation_result.status.value if result.validation_result else 'unknown',
        'status_message': result.validation_result.message if result.validation_result else None,
        'analysis_time_ms': int((time.time() - start_time) * 1000),
        'risk_level': 'LOW' if result.success else 'HIGH',
        'security_checks': {
            'length_ok': len(expression) <= evaluator.MAX_EXPRESSION_LENGTH,
            'nesting_ok': True,  # 已在验证中检查
            'node_count_ok': (result.node_count or 0) <= evaluator.MAX_NODE_COUNT,
            'execution_time_ok': (result.execution_time_ms or 0) <= evaluator.MAX_EXECUTION_TIME_MS,
        },
        'suggestions': []
    }
    
    if not result.success:
        analysis['suggestions'].append(f"修复错误: {result.error}")
    
    if len(expression) > evaluator.MAX_EXPRESSION_LENGTH // 2:
        analysis['suggestions'].append("表达式较长，建议简化")
    
    if (result.node_count or 0) > evaluator.MAX_NODE_COUNT // 2:
        analysis['suggestions'].append("表达式复杂度较高，建议优化")
    
    return analysis