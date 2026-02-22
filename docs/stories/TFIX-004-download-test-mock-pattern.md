# TFIX-004: Corrigir mock de fs/promises no download.test.ts

**Status:** Pending
**Prioridade:** Média
**Estimativa:** 30min
**Arquivos afetados:** 1 test file

## Problema

4 testes de download no modo filesystem (legacy) falham — a rota retorna 404 em vez de 200, `Content-Disposition` é null, e `readFile` nunca é chamado.

## Causa Raiz

O mock pattern de `fs/promises` no teste usa closure incorreta:

```typescript
const mockReadFile = jest.fn();  // Declarado fora do factory

jest.mock("fs/promises", () => ({
  readFile: (...args) => mockReadFile(...args),  // Closure potencialmente stale
}));
```

Quando o módulo da rota importa `readFile` de `fs/promises`, a referência do mock pode não estar corretamente vinculada devido ao hoisting do Jest. O `readFile()` falha silenciosamente, o catch block retorna 404.

## Testes que serão corrigidos

- `download.test.ts`: 4 falhas no bloco "Filesystem download (legacy mode)"
  - `should return 200 with Excel content when file exists`
  - `should set Content-Disposition with app name and current date`
  - `should use fallback app name when NEXT_PUBLIC_APP_NAME is unset`
  - `should call readFile with correct path based on UUID`

## Critérios de Aceitação

- [ ] AC1: Mock de `fs/promises` usa pattern correto (import depois do mock)
- [ ] AC2: 4 testes de filesystem download passam
- [ ] AC3: 13 testes de proxy download continuam passando (17/17 total)

## Solução

Corrigir o mock pattern:

```typescript
jest.mock("fs/promises", () => ({
  readFile: jest.fn(),
}));

import { readFile } from "fs/promises";
const mockReadFile = readFile as jest.Mock;
```

Ou usar `jest.spyOn`:
```typescript
import * as fsPromises from "fs/promises";
jest.spyOn(fsPromises, "readFile").mockResolvedValue(Buffer.from("excel"));
```

## Arquivos

- `frontend/__tests__/api/download.test.ts` — corrigir mock pattern
