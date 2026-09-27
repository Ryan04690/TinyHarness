class RecentContextPolicy:
    """
    Start deleting from the oldest complete interaction
    block until the Context can fit.
    """

    # -----------------------------------------------------
    # Split messages into:
    #
    # 1. pinned prefix
    #    - leading system messages
    #    - initial user request
    #
    # 2. removable interaction blocks
    #    - assistant
    #    - assistant + corresponding tool results
    # -----------------------------------------------------
    def _split_messages(
        self,
        messages,
    ):
        prefix = []
        blocks = []

        index = 0

        # Preserve leading system messages.
        # Laying the groundwork for future development.
        while (
            index < len(messages)
            and messages[index].get("role")
            == "system"
        ):
            prefix.append(messages[index])
            index += 1

        # Preserve the initial user request.
        if (
            index < len(messages)
            and messages[index].get("role")
            == "user"
        ):
            prefix.append(messages[index])
            index += 1

        # Group the remaining trajectory.
        while index < len(messages):
            message = messages[index]

            if (message.get("role")== "assistant"):
                block = [message]
                index += 1

                # Tool results belong to the
                # preceding assistant Tool Call.
                #
                # If one assistant message contains
                # multiple Tool Calls, all following
                # Tool results stay in the same block.
                while (
                    index < len(messages)and messages[index].get("role")== "tool"):
                    block.append(messages[index])
                    index += 1

                blocks.append(block)

            else:
                blocks.append([message])
                index += 1

        return prefix, blocks

    # -----------------------------------------------------
    # Apply Recent Context Policy
    # -----------------------------------------------------
    def apply(
        self,
        messages,
        tools,
        token_counter,
        context_budget,
        trace=None,
        step=None,
    ):
        if not messages:
            return []

        # Never mutate AgentState.messages.
        original_messages = list(messages)

        estimate = (
            token_counter.count_request(
                messages=original_messages,
                tools=tools,
            )
        )

        check = context_budget.check(estimate.total)

        # Already fits: no truncation.
        if check.within_budget:
            return original_messages

        prefix, blocks = (
            self._split_messages(
                original_messages
            )
        )

        remaining_blocks = list(blocks)

        # Remove the oldest complete interaction
        # block until the Context can fit.
        while remaining_blocks:
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

            # Remove the oldest complete block.
            remaining_blocks.pop(0)

        # Minimum possible Context:
        # pinned prefix only.
        return list(prefix)


class SummaryContextPolicy(
    RecentContextPolicy
):
    """
    Compress old interaction blocks into a summary
    instead of simply deleting them.
    """

    def __init__(
        self,
        summarizer,
    ):
        self.summarizer = summarizer

    # -----------------------------------------------------
    # Flatten:
    #
    # [
    #     [message1, message2],
    #     [message3, message4],
    # ]
    #
    # into:
    #
    # [
    #     message1,
    #     message2,
    #     message3,
    #     message4,
    # ]
    # -----------------------------------------------------
    def _flatten_blocks(
        self,
        blocks,
    ):
        return [
            message
            for block in blocks
            for message in block
        ]

    # -----------------------------------------------------
    # Convert summary text into a normal context message.
    #
    # We deliberately use role="assistant" instead of
    # role="system" because the summary comes from previous
    # assistant/tool execution history and should not be
    # promoted to system-level authority.
    # -----------------------------------------------------
    def _summary_message(
        self,
        summary,
    ):
        return {
            "role": "assistant",
            "content": (
                "[Earlier execution summary]\n"
                f"{summary}"
            ),
        }

    # -----------------------------------------------------
    # Run summarizer and record the summary call in Trace.
    #
    # Summary calls are real model calls, but they are
    # Context Maintenance Calls rather than Agent Decisions.
    # Therefore they do NOT increment AgentState.steps.
    # -----------------------------------------------------
    def _summarize(
        self,
        messages,
        trace=None,
        step=None,
    ):
        if trace is not None:
            trace.record(
                "context_summary_start",
                step=step,
                source_message_count=(
                    len(messages)
                ),
            )

        summary = (
            self.summarizer.summarize(messages)
        )

        if trace is not None:
            trace.record(
                "context_summary_end",
                step=step,
                source_message_count=(len(messages)),
                summary=summary,
            )

        return summary

    # -----------------------------------------------------
    # Apply Summary Context Policy
    # -----------------------------------------------------
    def apply(
        self,
        messages,
        tools,
        token_counter,
        context_budget,
        trace=None,
        step=None,
    ):
        if not messages:
            return []

        # Never mutate AgentState.messages.
        original_messages = list(messages)

        estimate = (
            token_counter.count_request(
                messages=original_messages,
                tools=tools,
            )
        )

        # Already fits: no summarization.
        if (
            context_budget
            .check(estimate.total)
            .within_budget
        ):
            return original_messages

        prefix, blocks = (
            self._split_messages(original_messages)
        )

        remaining_blocks = list(blocks)

        dropped_blocks = []

        # -------------------------------------------------
        # Gradually move old blocks into the summary.
        #
        # Example:
        #
        # USER + A + B + C
        #
        # becomes:
        #
        # USER + summary(A) + B + C
        #
        # If it still does not fit:
        #
        # USER + summary(A+B) + C
        # -------------------------------------------------
        while remaining_blocks:
            dropped_blocks.append(
                remaining_blocks.pop(0)
            )

            dropped_messages = (
                self._flatten_blocks(dropped_blocks)
            )

            summary = self._summarize(
                messages=dropped_messages,
                trace=trace,
                step=step,
            )

            summary_message = (
                self._summary_message(summary)
            )

            candidate = (
                prefix
                + [summary_message]
                + self._flatten_blocks(
                    remaining_blocks
                )
            )

            candidate_estimate = (
                token_counter.count_request(
                    messages=candidate,
                    tools=tools,
                )
            )

            if (
                context_budget
                .check(candidate_estimate.total)
                .within_budget
            ):
                return candidate

        # If we reach here, even:
        #
        # prefix + summary(all removable blocks)
        #
        # did not fit.
        #
        # Do NOT call the summarizer again here.
        # The last iteration above already summarized
        # all removable blocks and checked that candidate.
        #
        # Fall back to the smallest pinned Context.
        return list(prefix)