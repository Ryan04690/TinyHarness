class RecentContextPolicy:  # Start deleting from the oldest complete interaction block until the Context can fit.
    def _split_messages(
        self,
        messages,
    ):
        prefix = []
        blocks = []

        index = 0

        # Preserve leading system messages
        while (
            index < len(messages)
            and messages[index].get("role")
            == "system"  # Laying the groundwork for future development
        ):
            prefix.append(messages[index])
            index += 1

        # Preserve the initial user request
        if (
            index < len(messages)
            and messages[index].get("role")
            == "user"
        ):
            prefix.append(messages[index])
            index += 1

        # Group the remaining trajectory
        while index < len(messages):

            message = messages[index]

            if ( message.get("role") == "assistant" ):
                block = [message]
                index += 1

                # Tool results belong to the
                # preceding assistant Tool Call.
                while (
                    index < len(messages)
                    and messages[index].get(
                        "role"
                    )
                    == "tool"
                ):
                    block.append(messages[index])
                    index += 1

                blocks.append(block)

            else:
                blocks.append([message])
                index += 1

        return prefix, blocks

    def apply(
        self,
        messages,
        tools,
        token_counter,
        context_budget,
    ):
        if not messages:
            return []

        # Never mutate AgentState.messages
        original_messages = list(messages)

        estimate = (
            token_counter.count_request(
                messages=original_messages,
                tools=tools,
            )
        )

        check = context_budget.check(estimate.total)

        # Already fits: no truncation
        if check.within_budget:
            return original_messages

        prefix, blocks = (
            self._split_messages(
                original_messages
            )
        )

        remaining_blocks = list(blocks)

        while remaining_blocks:  # Loop

            candidate = (
                prefix
                + [
                    message
                    for block
                    in remaining_blocks
                    for message
                    in block
                ]
            )

            estimate = (
                token_counter.count_request(
                    messages=candidate,
                    tools=tools,
                )
            )

            if (
                context_budget
                .check(estimate.total)
                .within_budget
            ):
                return candidate

            # Remove the oldest complete block
            remaining_blocks.pop(0)

        # Minimum possible context:
        # pinned prefix only.
        return list(prefix)